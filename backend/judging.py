"""Private judging ASGI gateway. Local installations keep their original entry point."""
import asyncio
import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from functools import partial
import hmac
from http.cookies import SimpleCookie
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import threading
import time
from urllib.parse import urlparse
import uuid

from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse, Response
from pypdf import apply_configuration

from .demo_control import DemoLedger, MeteredProvider
from .extraction import SAMPLE_PATH
from .main import ROOT, create_app, public_job
from .models import CourseInput, GenerateInput
from .provider import NebiusProvider

COOKIE = "easy_street_judging"


async def acquire_write_gate(lock, timeout=10):
    # Cancellation must never strand a background thread that later takes ownership.
    deadline = time.monotonic()+timeout
    while not lock.acquire(blocking=False):
        if time.monotonic() >= deadline:
            return False
        await asyncio.sleep(.02)
    return True


def password_hash(password, salt=None):
    if len(password) < 12:
        raise ValueError("Use a judge access code with at least 12 characters.")
    salt = salt or secrets.token_bytes(24)
    digest = hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000)
    return "pbkdf2_sha256$310000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def check_password(password, encoded):
    try:
        algorithm, iterations, salt, wanted = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or int(iterations) != 310000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256",password.encode(),base64.b64decode(salt,validate=True),310000)
        return hmac.compare_digest(actual,base64.b64decode(wanted,validate=True))
    except (ValueError,TypeError):
        return False


def parse_time(value):
    parsed = datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Expiration times must include a timezone.")
    return parsed.timestamp()


@dataclass
class DemoSettings:
    origin: str
    data_dir: Path
    password_hash: str
    budget_limit: float = 0
    operator_token: str = ""
    retention_hours: int = 24
    max_sessions: int = 100
    max_concurrent: int = 2
    session_budget: float = .5
    max_upload_mib: int = 5
    max_modules: int = 3
    max_assignments: int = 3
    max_quizzes: int = 3
    allow_http: bool = False
    expires_at: str = "2026-12-16T08:00:00Z"
    credit_expires_at: str = ""
    max_storage_mib: int = 700

    def __post_init__(self):
        parsed = urlparse(self.origin)
        if (parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment or "*" in parsed.netloc):
            raise ValueError("Set the exact judging origin without a path or wildcard.")
        if parsed.scheme != "https" and not (self.allow_http and parsed.hostname in ("127.0.0.1","localhost")):
            raise ValueError("Judging requires HTTPS; HTTP is only allowed explicitly on localhost for tests.")
        if not self.password_hash.startswith("pbkdf2_sha256$310000$"):
            raise ValueError("Configure a hashed private judge access code before starting the demo.")
        if self.operator_token and len(self.operator_token) < 32:
            raise ValueError("The operator status token must have at least 32 characters.")
        for value, low, high in ((self.retention_hours,1,48),(self.max_sessions,1,200),
                (self.max_concurrent,1,4),(self.max_upload_mib,1,15),(self.max_modules,1,6),
                (self.max_assignments,0,6),(self.max_quizzes,0,6),(self.max_storage_mib,50,10000)):
            if type(value) is not int or not low <= value <= high:
                raise ValueError("A judging limit is outside its supported range.")
        if not math.isfinite(self.session_budget) or not 0 <= self.session_budget <= 10:
            raise ValueError("Choose a finite visitor budget between zero and ten USD.")
        parse_time(self.expires_at)
        if self.credit_expires_at:
            parse_time(self.credit_expires_at)
        self.data_dir = Path(self.data_dir).resolve()

    @classmethod
    def from_env(cls):
        prefix = "EASY_STREET_DEMO_"
        return cls(origin=os.environ.get(prefix+"ORIGIN",""),
            data_dir=Path(os.environ.get(prefix+"DATA_DIR",ROOT/"judging-data")),
            password_hash=os.environ.get("EASY_STREET_JUDGE_PASSWORD_HASH",""),
            operator_token=os.environ.get("EASY_STREET_OPERATOR_TOKEN",""),
            budget_limit=float(os.environ.get(prefix+"BUDGET_USD","0")),
            session_budget=float(os.environ.get(prefix+"SESSION_BUDGET_USD","0.5")),
            retention_hours=int(os.environ.get(prefix+"RETENTION_HOURS","24")),
            max_sessions=int(os.environ.get(prefix+"MAX_SESSIONS","100")),
            max_concurrent=int(os.environ.get(prefix+"MAX_CONCURRENT","2")),
            max_upload_mib=int(os.environ.get(prefix+"MAX_UPLOAD_MIB","5")),
            max_modules=int(os.environ.get(prefix+"MAX_MODULES","3")),
            max_assignments=int(os.environ.get(prefix+"MAX_ASSIGNMENTS","3")),
            max_quizzes=int(os.environ.get(prefix+"MAX_QUIZZES","3")),
            max_storage_mib=int(os.environ.get(prefix+"MAX_STORAGE_MIB","700")),
            allow_http=os.environ.get(prefix+"ALLOW_HTTP","0") == "1",
            expires_at=os.environ.get(prefix+"EXPIRES_AT","2026-12-16T08:00:00Z"),
            credit_expires_at=os.environ.get("NEBIUS_CREDIT_EXPIRES_AT",""))


class JudgingApplication:
    def __init__(self, settings: DemoSettings, provider=None, clock=time.time):
        self.settings, self.clock = settings, clock
        self.provider = provider or NebiusProvider()
        self.root = settings.data_dir
        self.tenants = self.root/"visitors"
        self.tenants.mkdir(parents=True,exist_ok=True)
        self.db_path = self.root/"sessions.sqlite3"
        self.ledger = DemoLedger(self.root/"operator-usage.sqlite3",settings.budget_limit,settings.max_concurrent)
        self.lock = threading.RLock()
        self.write_gate = threading.Lock()
        self.children, self.active, self.rates = {}, {}, {}
        self.web_slots = threading.BoundedSemaphore(16)
        self.stop_event = threading.Event()
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,id TEXT UNIQUE NOT NULL,
                    csrf TEXT NOT NULL,expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS samples(session_id TEXT,idem TEXT,course_id TEXT,job_id TEXT,
                    PRIMARY KEY(session_id,idem));
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path,timeout=20)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def rate(self, key, maximum):
        now = self.clock()
        with self.lock:
            self.rates = {name:times for name,times in self.rates.items() if times and times[-1] > now-60}
            if key not in self.rates and len(self.rates) >= 2048:
                return False
            values = [value for value in self.rates.get(key,[]) if value > now-60]
            if len(values) >= maximum:
                return False
            self.rates[key] = values+[now]
            return True

    def session(self, request):
        cookie = SimpleCookie()
        try:
            cookie.load(request.headers.get("cookie",""))
            raw = cookie[COOKIE].value if COOKIE in cookie else ""
        except Exception:
            raw = ""
        if not raw or len(raw) > 200:
            return None
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.connect() as db:
            row = db.execute("SELECT * FROM sessions WHERE token_hash=? AND expires>?",(digest,self.clock())).fetchone()
        return dict(row) if row else None

    def session_info(self, session=None):
        return {"mode":"judging","authenticated":session is not None,
                "retention_hours":self.settings.retention_hours,
                "expires_at":datetime.fromtimestamp(session["expires"],timezone.utc).isoformat() if session else None,
                **({"csrf_token":session["csrf"]} if session else {})}

    def child(self, session):
        with self.lock:
            if session["id"] not in self.children:
                self.children[session["id"]] = create_app(data_dir=self.tenants/session["id"],
                    providers={"nebius":MeteredProvider(self.provider,self.ledger,session["id"])},
                    budget_limit=self.settings.session_budget,allowed_origins=[self.settings.origin],
                    allowed_hosts=[urlparse(self.settings.origin).hostname],hosting_mode="judging")
                self.children[session["id"]].state.demo_info = {"retention_hours":self.settings.retention_hours,
                    "max_upload_mib":self.settings.max_upload_mib,"max_modules":self.settings.max_modules,
                    "max_assignments":self.settings.max_assignments,"max_quizzes":self.settings.max_quizzes}
                def document_guard(value, original_size):
                    if (len(value["passages"]) > 1000 or sum(len(p["text"]) for p in value["passages"]) > 100000
                            or len(json.dumps(value).encode()) > 2*1024*1024):
                        raise ValueError("This judging demo accepts one readable chapter: at most 100,000 characters and 1,000 passages. Use a local installation for larger documents.")
                self.children[session["id"]].state.service.document_guard = document_guard
                # Hosted chapter parsing has smaller per-stream expansion/work bounds.
                # pypdf's context-local configuration leaves local installations unchanged.
                stream_limit = 8*1024*1024
                self.children[session["id"]].state.service.extraction_context = partial(apply_configuration,
                    maximum_declared_stream_length=stream_limit,array_based_stream_maximum_output_length=stream_limit,
                    jbig2_maximum_output_length=stream_limit,lzw_maximum_output_length=stream_limit,
                    run_length_maximum_output_length=stream_limit,zlib_maximum_output_length=stream_limit,
                    brotli_maximum_output_length=stream_limit,image_maximum_buffer_size=stream_limit,
                    stream_decoding_work_maximum_length=32*1024*1024,page_tree_maximum_entries=1000)
            return self.children[session["id"]]

    def erase(self, session):
        # Caller owns lock; never remove a directory while a worker is using it.
        if self.active.get(session["id"],0):
            return False
        self.children.pop(session["id"],None)
        directory = self.tenants/session["id"]
        if directory.is_symlink() or directory.resolve().parent != self.tenants.resolve():
            raise RuntimeError("Unsafe temporary workspace path.")
        if directory.exists():
            shutil.rmtree(directory)
        with self.connect() as db:
            db.execute("DELETE FROM samples WHERE session_id=?",(session["id"],))
            db.execute("DELETE FROM sessions WHERE id=?",(session["id"],))
        # The operator ledger intentionally contains no source, answers, or key.
        return True

    def cleanup(self):
        with self.lock:
            with self.connect() as db:
                expired = [dict(row) for row in db.execute("SELECT * FROM sessions WHERE expires<=?",(self.clock(),))]
                known = {row[0] for row in db.execute("SELECT id FROM sessions")}
            for session in expired:
                self.erase(session)
            for directory in self.tenants.iterdir():
                if directory.name not in known and not self.active.get(directory.name,0) and directory.is_dir() and not directory.is_symlink():
                    if directory.resolve().parent == self.tenants.resolve():
                        shutil.rmtree(directory)

    def maintenance(self):
        while not self.stop_event.wait(60):
            try:
                self.cleanup()
            except Exception:
                # No raw exception or visitor data is logged. Operator status reports failure.
                self.cleanup_failed = True

    async def lifespan(self, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                self.cleanup_failed = False
                self.cleanup()
                self.thread = threading.Thread(target=self.maintenance,daemon=True)
                self.thread.start()
                await send({"type":"lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                self.stop_event.set()
                if hasattr(self,"thread"):
                    self.thread.join(timeout=2)
                await send({"type":"lifespan.shutdown.complete"})
                return

    async def body(self, receive, maximum, timeout=60):
        result = bytearray()
        deadline = asyncio.get_running_loop().time()+timeout
        while True:
            remaining = deadline-asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError()
            message = await asyncio.wait_for(receive(),timeout=remaining)
            if message["type"] == "http.disconnect":
                raise ValueError("Disconnected request.")
            result.extend(message.get("body",b""))
            if len(result) > maximum:
                raise OverflowError()
            if not message.get("more_body",False):
                return bytes(result)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.lifespan(receive,send)
        if scope["type"] != "http":
            return
        request = Request(scope)
        async def protected_send(message):
            if message["type"] == "http.response.start":
                additions = {b"cache-control":b"no-store",b"x-content-type-options":b"nosniff",b"referrer-policy":b"no-referrer",
                    b"content-security-policy":b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"}
                headers = [(k,v) for k,v in message.get("headers",[]) if k.lower() not in additions]
                message = {**message,"headers":headers+list(additions.items())}
            await send(message)
        async def reply(data, status=200, headers=None):
            return await JSONResponse(data,status_code=status,headers=headers)(scope,receive,protected_send)
        parsed = urlparse(self.settings.origin)
        # Internal platform probes have no visitor data and may use localhost Host.
        if request.url.path in ("/health/live","/health/ready") and request.method == "GET":
            configured = self.provider.key_configured
            return await reply({"status":"ok" if request.url.path.endswith("live") or configured else "not_ready",
                "generation_available":configured and self.ledger.snapshot()["remaining_usd"] > 0 and self.clock() < parse_time(self.settings.expires_at)},
                200 if request.url.path.endswith("live") or configured else 503)
        if request.headers.get("host","").lower() != parsed.netloc.lower():
            return await reply({"detail":"Unrecognized demo host."},400)
        origin = request.headers.get("origin")
        if (origin and origin != self.settings.origin) or (request.headers.get("sec-fetch-site") == "cross-site" and request.url.path.startswith("/api/")):
            return await reply({"detail":"Cross-origin demo requests are blocked."},403)
        path = request.url.path
        if path == "/api/operator/status" and request.method == "GET":
            wanted = self.settings.operator_token
            if not wanted or not hmac.compare_digest(request.headers.get("authorization",""),"Bearer "+wanted):
                return await reply({"detail":"Operator authentication required."},401)
            budget = self.ledger.snapshot()
            provider_health = self.ledger.provider_health()
            provider_failed = any(stage["state"] == "failing" for stage in provider_health.values())
            low = budget["remaining_usd"] <= max(.10,self.settings.budget_limit*.2)
            expired_credit = bool(self.settings.credit_expires_at and parse_time(self.settings.credit_expires_at) <= self.clock()+7*86400)
            expiring = parse_time(self.settings.expires_at) <= self.clock()+7*86400
            return await reply({"budget":budget,"provider_configured":self.provider.key_configured,
                "provider_health":provider_health,
                "needs_attention":low or expired_credit or expiring or provider_failed or budget["uncertain_calls"] > 0 or not self.provider.key_configured or getattr(self,"cleanup_failed",False),
                "low_application_allowance":low,"credit_expiry_within_seven_days":expired_credit,
                "deployment_expiry_within_seven_days":expiring,
                "credit_expiry_known":bool(self.settings.credit_expires_at),
                "provider_balance_verified":False,"cleanup_failed":getattr(self,"cleanup_failed",False),
                "notice":"Application allowance is not provider credit balance. Exhaustion interrupts judging; an operator must intervene."})
        if not path.startswith("/api/"):
            if request.method not in ("GET","HEAD"):
                return await reply({"detail":"Method not allowed."},405)
            relative = "index.html" if path == "/" else path.lstrip("/")
            asset = (ROOT/"frontend/dist"/relative).resolve()
            if path == "/sample-license.txt":
                asset = ROOT/"backend/sample/LICENSE.txt"
            elif not asset.is_relative_to((ROOT/"frontend/dist").resolve()):
                return await reply({"detail":"File not found."},404)
            if not asset.is_file():
                return await reply({"detail":"File not found. Build the interface before starting."},404)
            return await FileResponse(asset)(scope,receive,protected_send)
        if self.clock() >= parse_time(self.settings.expires_at):
            return await reply({"detail":"This temporary judging deployment has ended. Contact the operator."},503)
        if not self.web_slots.acquire(blocking=False):
            return await reply({"detail":"The demo is busy. Please try again shortly."},429,{"Retry-After":"10"})
        try:
            return await self.api(request,scope,receive,protected_send,reply)
        except OverflowError:
            return await reply({"detail":"Upload exceeds this demo's bounded request limit."},413)
        except asyncio.TimeoutError:
            return await reply({"detail":"The request took too long to upload. Please retry on a stable connection."},408,{"Connection":"close"})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError):
            return await reply({"detail":"Invalid demo request. Check the required fields."},400)
        finally:
            self.web_slots.release()

    async def api(self, request, scope, receive, send, reply):
        path, method = request.url.path, request.method
        session = self.session(request)
        if path == "/api/session" and method == "GET":
            return await reply(self.session_info(session))
        if path == "/api/session" and method == "POST":
            client = hashlib.sha256(str(scope.get("client",("unknown",0))[0]).encode()).hexdigest()
            if not self.rate("login:"+client,8) or not self.rate("login:global",60):
                return await reply({"detail":"Too many access attempts. Wait one minute."},429,{"Retry-After":"60"})
            body = json.loads(await self.body(receive,4096,timeout=10))
            password = body.get("access_code","")
            if not isinstance(password,str) or len(password) > 1000 or not await asyncio.to_thread(check_password,password,self.settings.password_hash):
                return await reply({"detail":"That judge access code was not accepted."},401)
            with self.lock:
                self.cleanup()
                with self.connect() as db:
                    if db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] >= self.settings.max_sessions:
                        return await reply({"detail":"Temporary visitor capacity is full. Contact the operator."},503)
                    token = secrets.token_urlsafe(40)
                    session = {"id":uuid.uuid4().hex,"csrf":secrets.token_urlsafe(32),
                        "expires":min(self.clock()+self.settings.retention_hours*3600,parse_time(self.settings.expires_at))}
                    db.execute("INSERT INTO sessions VALUES(?,?,?,?)",(hashlib.sha256(token.encode()).hexdigest(),session["id"],session["csrf"],session["expires"]))
            response = JSONResponse(self.session_info(session))
            response.set_cookie(COOKIE,token,httponly=True,secure=urlparse(self.settings.origin).scheme == "https",samesite="strict",
                                max_age=int(session["expires"]-self.clock()),path="/")
            return await response(scope,receive,send)
        if not session:
            return await reply({"detail":"Use the private judge access code to open a temporary workspace."},401)
        if method not in ("GET","HEAD","OPTIONS"):
            if not hmac.compare_digest(request.headers.get("x-easy-street-csrf",""),session["csrf"]):
                return await reply({"detail":"Refresh the page before changing this workspace."},403)
        with self.lock:
            # Recheck under the same lock as deletion so an earlier request cannot
            # resurrect a workspace after another request has erased it.
            with self.connect() as db:
                present = db.execute("SELECT 1 FROM sessions WHERE id=? AND expires>?",(session["id"],self.clock())).fetchone()
            if not present:
                return await reply({"detail":"This temporary workspace has ended. Open a new session."},401)
            if path == "/api/session" and method == "DELETE":
                if not self.erase(session):
                    return await reply({"detail":"Generation is still finishing. Cancel it, then retry deletion when it stops."},409)
                response = JSONResponse({"deleted":True})
                response.delete_cookie(COOKIE,path="/",httponly=True,secure=urlparse(self.settings.origin).scheme == "https",samesite="strict")
                return await response(scope,receive,send)
            self.active[session["id"]] = self.active.get(session["id"],0)+1
        try:
            if not self.rate("session:"+session["id"],120):
                return await reply({"detail":"Too many workspace requests. Wait one minute."},429,{"Retry-After":"60"})
            child = self.child(session)
            service = child.state.service
            body = b""
            gate_held = False
            if method in ("POST","PUT","PATCH","DELETE"):
                body = await self.body(receive,self.settings.max_upload_mib*1024*1024+65536)
                if not await acquire_write_gate(self.write_gate):
                    return await reply({"detail":"The demo is busy saving work. Try again shortly."},429,{"Retry-After":"10"})
                gate_held = True
                # Serialize bounded mutations until response completion, without
                # holding the gate during subsequent inference background tasks.
                local_bytes = sum(p.stat().st_size for p in (self.tenants/session["id"]).rglob("*") if p.is_file())
                total_bytes = sum(p.stat().st_size for p in self.tenants.rglob("*") if p.is_file())
                if local_bytes+len(body)+8*1024*1024 > 32*1024*1024 or total_bytes+len(body)+24*1024*1024 > self.settings.max_storage_mib*1024*1024:
                    return await reply({"detail":"Temporary storage is full. Export and delete your workspace or contact the operator."},413)
            original_send = send
            async def release_after_response(message):
                nonlocal gate_held
                await original_send(message)
                if message["type"] == "http.response.body" and not message.get("more_body",False) and gate_held:
                    self.write_gate.release()
                    gate_held = False
            send = release_after_response
            if path == "/api/courses" and method == "POST":
                if len(service.store.all("courses")) >= 12:
                    return await reply({"detail":"Export and delete this temporary workspace before creating more courses."},413)
                values = json.loads(body)
                if values.get("mode","nebius") not in ("nebius","demo"):
                    return await reply({"detail":"This judging deployment uses Nebius. OpenAI remains available in local installations."},422)
                for field, cap in (("modules",self.settings.max_modules),("assignments",self.settings.max_assignments),("quizzes",self.settings.max_quizzes)):
                    if type(values.get(field,1)) is not int or values.get(field,1) > cap:
                        return await reply({"detail":f"This judging demo supports up to {cap} {field} per course."},422)
                values.setdefault("mode","nebius")
                body = json.dumps(values).encode()
            if path == "/api/courses/import" and method == "POST":
                return await reply({"detail":"Import backups in a local installation. Judging workspaces accept source uploads and export backups."},422)
            if method == "POST" and (path in ("/api/documents","/api/documents/sample") or path.endswith("/source")):
                count = len(service.store.all("documents"))
                if count >= 5:
                    return await reply({"detail":"This temporary workspace holds up to five sources. Export and delete it before starting another."},413)
                local_bytes = sum(p.stat().st_size for p in (self.tenants/session["id"]).rglob("*") if p.is_file())
                total_bytes = sum(p.stat().st_size for p in self.tenants.rglob("*") if p.is_file())
                if local_bytes+len(body) > 32*1024*1024 or total_bytes+len(body) > self.settings.max_storage_mib*1024*1024:
                    return await reply({"detail":"Temporary storage is full. Delete unused workspaces or contact the operator."},413)
            if path == "/api/sample-course" and method == "POST":
                return await self.sample(session,service,json.loads(body),scope,receive,send,reply)
            delivered = False
            async def replay():
                nonlocal delivered
                if not delivered and method in ("POST","PUT","PATCH","DELETE"):
                    delivered = True
                    return {"type":"http.request","body":body,"more_body":False}
                return await receive()
            return await child(scope,replay,send)
        finally:
            if locals().get("gate_held"):
                self.write_gate.release()
            with self.lock:
                self.active[session["id"]] -= 1

    async def sample(self, session, service, body, scope, receive, send, reply):
        if body.get("provider_disclosure_accepted") is not True:
            return await reply({"detail":"Approve sending the original sample excerpts to Nebius first."},422)
        idem = body.get("idempotency_key")
        if not isinstance(idem,str) or not 8 <= len(idem) <= 100:
            return await reply({"detail":"A bounded request identifier is required."},422)
        fresh = False
        with self.lock:
            with self.connect() as db:
                existing = db.execute("SELECT * FROM samples WHERE session_id=? AND idem=?",(session["id"],idem)).fetchone()
                if existing:
                    course = service.store.get("courses",existing["course_id"])
                    job = service.store.get("jobs",existing["job_id"])
                    document = service.store.get("documents",course["document_id"])
                else:
                    if len(service.store.all("courses")) >= 12:
                        return await reply({"detail":"Export and delete this temporary workspace before creating more courses."},413)
                    document = service.document(SAMPLE_PATH.read_bytes(),"small-garden-watering.txt")
                    course = service.create_course(CourseInput(document_id=document["id"],title="Small Garden Watering — Nemotron sample",mode="nebius",
                        assignments=min(1,self.settings.max_assignments),quizzes=min(1,self.settings.max_quizzes)))
                    course.update(outline_approved=True,status="ready")
                    service.store.put_course(course,"Before sample approval")
                    job,fresh = service.submit(course["id"],GenerateInput(idempotency_key=hashlib.sha256((session["id"]+idem).encode()).hexdigest()))
                    db.execute("INSERT INTO samples VALUES(?,?,?,?)",(session["id"],idem,course["id"],job["id"]))
        response = JSONResponse({"course":course,"document":document,"job":public_job(job)},
            background=BackgroundTask(service.run,job["id"]) if fresh else None)
        return await response(scope,receive,send)
