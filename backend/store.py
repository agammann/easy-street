import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path, budget_limit: float):
        self.path = path
        self.budget_limit = budget_limit
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, sha256 TEXT UNIQUE, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS courses(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, course_id TEXT, created_at TEXT, reason TEXT, data TEXT);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, course_id TEXT, idem TEXT UNIQUE, reservation REAL NOT NULL DEFAULT 0, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, job_id TEXT, stage TEXT, model TEXT, input_tokens INTEGER, output_tokens INTEGER, cost_usd REAL, status TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS cache(key TEXT PRIMARY KEY, data TEXT NOT NULL);
            """)
            # OCR variants share the original file digest but have distinct document
            # identifiers. Migrate the first release's unique digest without loss.
            schema = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'").fetchone()[0]
            if "sha256 TEXT UNIQUE" in schema:
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE documents_variants(id TEXT PRIMARY KEY, sha256 TEXT, data TEXT NOT NULL);
                    INSERT INTO documents_variants SELECT id,sha256,data FROM documents;
                    DROP TABLE documents;
                    ALTER TABLE documents_variants RENAME TO documents;
                    CREATE INDEX documents_digest ON documents(sha256);
                    COMMIT;
                """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, table, id):
        with self.connect() as db:
            row = db.execute(f"SELECT data FROM {table} WHERE id=?", (id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def all(self, table):
        with self.connect() as db:
            return [json.loads(r["data"]) for r in db.execute(f"SELECT data FROM {table} ORDER BY rowid DESC")]

    def put_document(self, value):
        with self.connect() as db:
            existing = db.execute("SELECT data FROM documents WHERE id=?",(value["id"],)).fetchone()
            if existing and json.loads(existing[0]).get("source_missing"):
                db.execute("UPDATE documents SET sha256=?,data=? WHERE id=?",(value["sha256"],json.dumps(value),value["id"]))
            else:
                db.execute("INSERT OR IGNORE INTO documents VALUES (?,?,?)", (value["id"],value["sha256"],json.dumps(value)))

    def put_course(self, course, reason=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT data FROM courses WHERE id=?", (course["id"],)).fetchone()
            if old and reason:
                db.execute("INSERT INTO versions(course_id,created_at,reason,data) VALUES(?,?,?,?)", (course["id"],now(),reason,old["data"]))
            course["version"] = (json.loads(old["data"])["version"] + 1) if old else 1
            course["updated_at"] = now()
            db.execute("INSERT OR REPLACE INTO courses VALUES (?,?)", (course["id"],json.dumps(course)))

    def put_job(self, job, release=False):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT data FROM jobs WHERE id=?",(job["id"],)).fetchone()
            if current:
                # Cancellation is sticky. A worker updating an older stage snapshot
                # must not erase a cancellation that arrived after its last read.
                job["cancel_requested"] = job["cancel_requested"] or json.loads(current["data"])["cancel_requested"]
            if release:
                db.execute("UPDATE jobs SET data=?, reservation=0 WHERE id=?", (json.dumps(job),job["id"]))
            else:
                db.execute("UPDATE jobs SET data=? WHERE id=?", (json.dumps(job),job["id"]))

    def budget(self, db=None):
        if db is None:
            with self.connect() as db:
                return self.budget(db)
        spent = float(db.execute("SELECT COALESCE(SUM(cost_usd),0) FROM usage").fetchone()[0])
        reserved = float(db.execute("SELECT COALESCE(SUM(reservation),0) FROM jobs").fetchone()[0])
        return {"limit_usd":self.budget_limit,"spent_usd":round(spent,8),"reserved_usd":round(reserved,8),
                "remaining_usd":round(max(0,self.budget_limit-spent-reserved),8)}

    def reserve_job(self, job, idem, maximum):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT data FROM jobs WHERE idem=?",(idem,)).fetchone()
            if existing:
                return json.loads(existing["data"])
            if maximum > self.budget(db)["remaining_usd"]:
                raise ValueError("The next generation and verification calls do not fit the remaining application budget. Raise EASY_STREET_BUDGET_USD deliberately or use the offline sample.")
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?)",(job["id"],job["course_id"],idem,maximum,json.dumps(job)))
            return None

    def usage(self, job_id, stage, model, usage, cost, status="completed"):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO usage(job_id,stage,model,input_tokens,output_tokens,cost_usd,status,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (job_id,stage,model,usage.input_tokens,usage.output_tokens,cost,status,now()))
            if status == "completed":
                db.execute("UPDATE jobs SET reservation=MAX(0,reservation-?) WHERE id=?",(cost,job_id))

    def ensure_call_budget(self, job_id, maximum):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            reserved = db.execute("SELECT reservation FROM jobs WHERE id=?",(job_id,)).fetchone()[0]
            extra = max(0,maximum-reserved)
            if extra > self.budget(db)["remaining_usd"]:
                raise ValueError("The next provider call does not fit the remaining application budget.")
            db.execute("UPDATE jobs SET reservation=reservation+? WHERE id=?",(extra,job_id))

    def cache_get(self, key):
        with self.connect() as db:
            row = db.execute("SELECT data FROM cache WHERE key=?",(key,)).fetchone()
            return json.loads(row[0]) if row else None

    def cache_put(self, key, value):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)",(key,json.dumps(value)))

    def histories(self, id):
        with self.connect() as db:
            return [{"id":r["id"],"created_at":r["created_at"],"reason":r["reason"],"course":json.loads(r["data"])}
                    for r in db.execute("SELECT * FROM versions WHERE course_id=? ORDER BY id DESC",(id,))]

    def usage_records(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM usage ORDER BY id DESC")]
