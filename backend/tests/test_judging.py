"""Private-demo gateway tests with temporary workspaces and mocked inference only."""
from concurrent.futures import ThreadPoolExecutor
import asyncio
import io
from datetime import datetime, timezone
import json
import sqlite3
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from pypdf import PdfReader, PdfWriter, get_configuration
from pypdf.generic import DecodedStreamObject, NameObject

from backend.demo_control import DemoLedger, MeteredProvider
from backend.extraction import ExtractionError, SAMPLE_PATH
from backend.judging import COOKIE, DemoSettings, JudgingApplication, acquire_write_gate, password_hash
from backend.models import GeneratedCourse, Verification
from backend.provider import (NEBIUS_MODEL, NEBIUS_PRICING, ProviderCallRejected,
                              ProviderOutputError, UsageCounts, cost)
from backend.service import Service


ACCESS_CODE = "private-test-access-code"
PASSWORD_HASH = password_hash(ACCESS_CODE,salt=b"deterministic-test-salt-only")
OPERATOR_TOKEN = "private-operator-test-token-at-least-32-characters"
NOW = datetime(2026,10,16,12,tzinfo=timezone.utc).timestamp()


class FakeProvider:
    name,model,pricing,key_configured = "nebius",NEBIUS_MODEL,NEBIUS_PRICING,True
    api_key = "never-export-this-fixture-key"

    def __init__(self):
        self.calls=[]
        self.lock=threading.Lock()
        self.in_flight=self.maximum_in_flight=0
        self.started=threading.Event()
        self.release=None
        self.delay=0
        self.failure=None

    def enter(self,stage,payload):
        with self.lock:
            self.calls.append(stage)
            self.in_flight+=1
            self.maximum_in_flight=max(self.maximum_in_flight,self.in_flight)
        self.started.set()
        if self.release is not None and not self.release.wait(10):
            raise AssertionError("The test must release its mocked provider.")
        if self.delay:
            time.sleep(self.delay)
        if self.failure:
            with self.lock:
                self.in_flight-=1
            raise self.failure

    def leave(self):
        with self.lock:
            self.in_flight-=1

    def generate(self,payload):
        self.enter("generation",payload)
        try:
            passage=payload["passages"][0]
            quote=passage["text"][:500]
            target=payload.get("target_section")
            options=payload["options"]
            kinds=([target["kind"]] if target else
                ["objectives","introduction","readings","notes","announcement"]+
                ["assignment"]*options["assignments"]+["rubric"]*options["assignments"]+
                ["quiz"]*(options["quizzes"]*options["questions_per_quiz"]))
            sections=[]
            for index,kind in enumerate(kinds):
                sections.append({"id":target["id"] if target else f"section-{index}","kind":kind,
                    "title":f"Source {kind}","body":quote,"answer":quote if kind == "quiz" else None,
                    "explanation":quote if kind == "quiz" else None,
                    "evidence":[{"passage_id":passage["id"],"quote":quote}]})
            return GeneratedCourse.model_validate({"sections":sections}),UsageCounts(100,40)
        finally:
            self.leave()

    def verify(self,payload):
        self.enter("verification",payload)
        try:
            return Verification(results=[{"section_id":section["id"],"status":"supported",
                "reason":"Deterministic source fixture; no live model was called."}
                for section in payload["sections"]]),UsageCounts(80,20)
        finally:
            self.leave()


@pytest.fixture
def gateway(tmp_path):
    provider=FakeProvider()
    clock=[NOW]
    settings=DemoSettings(origin="https://judge.example",data_dir=tmp_path,
        password_hash=PASSWORD_HASH,operator_token=OPERATOR_TOKEN,budget_limit=5,
        session_budget=1,retention_hours=24)
    app=JudgingApplication(settings,provider=provider,clock=lambda:clock[0])
    with TestClient(app,base_url=settings.origin) as client:
        yield app,client,provider,clock


def login(client):
    response=client.post("/api/session",json={"access_code":ACCESS_CODE})
    assert response.status_code == 200,response.text
    return {"cookie":f"{COOKIE}={response.cookies[COOKIE]}",
            "x-easy-street-csrf":response.json()["csrf_token"]}


def sample(client,headers,key="sample-request-001"):
    response=client.post("/api/sample-course",headers=headers,json={
        "provider_disclosure_accepted":True,"idempotency_key":key})
    assert response.status_code == 200,response.text
    return response.json()


def session_from(app,headers):
    return app.session(Request({"type":"http","headers":[(b"cookie",headers["cookie"].encode())]}))


def source_course(client,headers,mode="nebius",**options):
    document=client.post("/api/documents/sample",headers=headers)
    assert document.status_code == 200,document.text
    response=client.post("/api/courses",headers=headers,json={"document_id":document.json()["id"],
        "title":"A source course","mode":mode,**options})
    assert response.status_code == 200,response.text
    return document.json(),response.json()


def test_auth_cookie_private_workspace_and_public_health(gateway):
    app,client,provider,_=gateway
    assert client.get("/api/session").json()["authenticated"] is False
    assert client.get("/health/live",headers={"host":"localhost"}).status_code == 200
    assert client.get("/health/ready",headers={"host":"localhost"}).status_code == 200
    bad=client.post("/api/session",json={"access_code":"incorrect"})
    assert bad.status_code == 401 and provider.calls == []
    response=client.post("/api/session",json={"access_code":ACCESS_CODE})
    assert response.status_code == 200
    cookie=response.headers["set-cookie"].lower()
    assert "secure" in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert "max-age=" in cookie and "path=/" in cookie
    assert response.json()["authenticated"] is True
    assert ACCESS_CODE not in response.text and PASSWORD_HASH not in response.text
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("method,path,body",[
    ("get","/api/courses",None),("get","/api/documents",None),
    ("get","/api/config",None),("get","/api/usage",None),
    ("post","/api/documents/sample",{}),
    ("post","/api/sample-course",{"provider_disclosure_accepted":True,"idempotency_key":"unauthorized-request"}),
    ("post","/api/courses/unknown/generate",{"idempotency_key":"unauthorized-request"}),
])
def test_unauthenticated_api_cannot_read_or_request_inference(gateway,method,path,body):
    app,client,provider,_=gateway
    response=getattr(client,method)(path,**({"json":body} if body is not None else {}))
    assert response.status_code == 401
    assert provider.calls == []
    assert app.ledger.snapshot()["spent_usd"] == app.ledger.snapshot()["reserved_usd"] == 0


def test_csrf_origin_fetch_site_host_and_body_limits(gateway):
    _,client,provider,_=gateway
    headers=login(client)
    assert client.post("/api/documents/sample",headers={"cookie":headers["cookie"]}).status_code == 403
    assert client.post("/api/documents/sample",headers={**headers,"x-easy-street-csrf":"wrong"}).status_code == 403
    assert client.get("/api/courses",headers={**headers,"origin":"https://foreign.example"}).status_code == 403
    assert client.get("/api/courses",headers={**headers,"sec-fetch-site":"cross-site"}).status_code == 403
    assert client.get("/api/courses",headers={**headers,"host":"foreign.example"}).status_code == 400
    too_large=client.post("/api/documents",headers=headers,content=b"x"*(6*1024*1024))
    assert too_large.status_code == 413 and provider.calls == []


def test_login_and_session_rates_are_bounded_and_reset(gateway):
    app,client,provider,clock=gateway
    for _ in range(8):
        assert client.post("/api/session",json={"access_code":"incorrect"}).status_code == 401
    limited=client.post("/api/session",json={"access_code":ACCESS_CODE},headers={"x-forwarded-for":"198.51.100.25"})
    assert limited.status_code == 429 and limited.headers["retry-after"] == "60"
    clock[0]+=61
    headers=login(client)
    for _ in range(120):
        assert app.rate("session:"+session_from(app,headers)["id"],120)
    assert client.get("/api/courses",headers=headers).status_code == 429
    clock[0]+=61
    assert client.get("/api/courses",headers=headers).status_code == 200
    assert provider.calls == []


def test_one_click_duplicate_and_cache_do_not_repeat_provider_charges(gateway):
    app,client,provider,_=gateway
    headers=login(client)
    first=sample(client,headers)
    before=app.ledger.snapshot()
    repeated=sample(client,headers)
    assert repeated["course"]["id"] == first["course"]["id"]
    assert repeated["job"]["id"] == first["job"]["id"]
    cached=sample(client,headers,key="different-request-same-sample")
    assert cached["course"]["id"] != first["course"]["id"]
    assert provider.calls == ["generation","verification"]
    assert app.ledger.snapshot() == before
    assert client.get(f"/api/jobs/{first['job']['id']}",headers=headers).json()["status"] == "complete"
    assert len(client.get("/api/courses",headers=headers).json()) == 2


def test_session_isolation_for_sources_courses_jobs_versions_edits_and_exports(gateway):
    app,client,provider,_=gateway
    first=login(client)
    result=sample(client,first)
    course_id,doc_id,job_id=result["course"]["id"],result["document"]["id"],result["job"]["id"]
    course=client.get(f"/api/courses/{course_id}",headers=first).json()
    section_id=course["sections"][0]["id"]
    versions=client.get(f"/api/courses/{course_id}/versions",headers=first).json()
    assert versions
    second=login(client)
    assert session_from(app,first)["id"] != session_from(app,second)["id"]
    for path in ("/api/documents","/api/courses"):
        assert client.get(path,headers=second).json() == []
    for path in (f"/api/documents/{doc_id}",f"/api/courses/{course_id}",
                 f"/api/courses/{course_id}/versions",f"/api/courses/{course_id}/job",
                 f"/api/courses/{course_id}/estimate",f"/api/jobs/{job_id}"):
        assert client.get(path,headers=second).status_code == 404
    for kind in ("html","answers","json"):
        assert client.get(f"/api/courses/{course_id}/export?format={kind}",headers=second).status_code == 404
    requests=[("post",f"/api/courses/{course_id}/approve",{"provider_disclosure_accepted":True}),
        ("post",f"/api/courses/{course_id}/generate",{"idempotency_key":"another-visitor-generate"}),
        ("post",f"/api/courses/{course_id}/archive",{"archived":True}),
        ("post",f"/api/courses/{course_id}/restore",{"version_id":versions[0]["id"]}),
        ("post",f"/api/courses/{course_id}/reorder",{"section_ids":[section["id"] for section in course["sections"]]}),
        ("post",f"/api/jobs/{job_id}/cancel",{}),("post",f"/api/jobs/{job_id}/resume",{}),
        ("patch",f"/api/courses/{course_id}/outline",{"title":"Foreign edit"}),
        ("patch",f"/api/courses/{course_id}/sections/{section_id}",{"body":"Foreign edit"})]
    for method,path,body in requests:
        # Generation's existing Service boundary reports an unknown course as
        # a generic validation error; both paths must deny the foreign object.
        expected=400 if path.endswith("/generate") else 404
        assert getattr(client,method)(path,headers=second,json=body).status_code == expected
    assert client.post(f"/api/courses/{course_id}/source",headers=second,
        files={"file":("source.txt",b"A different original source with enough readable text.","text/plain")}).status_code == 404
    assert client.get("/api/usage",headers=second).json()["records"] == []
    assert client.get(f"/api/courses/{course_id}",headers=first).json() == course
    assert provider.calls == ["generation","verification"]


def test_regular_upload_configurable_counts_evidence_and_key_secrecy(gateway):
    app,client,provider,_=gateway
    headers=login(client)
    source=b"Garden observation\n\nObserve the soil before watering. Record whether the top layer feels dry.\n\nA second observation can differ from the first observation."
    upload=client.post("/api/documents",headers=headers,files={"file":("original.txt",source,"text/plain")})
    assert upload.status_code == 200
    assert client.post("/api/documents",headers=headers,files={"file":("original.txt",source,"text/plain")}).json()["cached"] is True
    created=client.post("/api/courses",headers=headers,json={"document_id":upload.json()["id"],
        "title":"Own original observations","mode":"nebius","modules":3,"assignments":3,"quizzes":3,"questions_per_quiz":2})
    assert created.status_code == 200
    course_id=created.json()["id"]
    assert client.post(f"/api/courses/{course_id}/approve",headers=headers,json={"provider_disclosure_accepted":True}).status_code == 200
    job=client.post(f"/api/courses/{course_id}/generate",headers=headers,json={"idempotency_key":"custom-upload-generation"})
    assert job.status_code == 200
    course=client.get(f"/api/courses/{course_id}",headers=headers).json()
    assert len(course["generated_module_ids"]) == 3
    assert sum(section["kind"] == "assignment" for section in course["sections"]) == 3
    assert sum(section["kind"] == "quiz" for section in course["sections"]) == 6
    passages={passage["id"]:passage["text"] for passage in upload.json()["passages"]}
    assert all(evidence["quote"] in passages[evidence["passage_id"]]
               for section in course["sections"] for evidence in section["evidence"])
    visible=[client.get(path,headers=headers).text for path in ("/api/config","/api/usage",f"/api/courses/{course_id}",
        f"/api/jobs/{job.json()['id']}",f"/api/courses/{course_id}/export?format=json")]
    assert all(provider.api_key not in value and OPERATOR_TOKEN not in value and PASSWORD_HASH not in value for value in visible)
    assert provider.api_key.encode() not in app.ledger.path.read_bytes()
    config=client.get("/api/config",headers=headers).json()
    assert config["provider"] == "nebius" and len(config["providers"]) == 1
    assert config["providers"][0]["key_configured"] is True


def test_zero_operator_budget_rejects_before_provider_and_does_not_hold_reservation(gateway):
    app,client,provider,_=gateway
    app.ledger.limit=0
    headers=login(client)
    result=sample(client,headers)
    job=client.get(f"/api/jobs/{result['job']['id']}",headers=headers).json()
    assert job["status"] == "failed"
    assert provider.calls == []
    assert app.ledger.snapshot()["spent_usd"] == app.ledger.snapshot()["reserved_usd"] == 0
    assert client.get("/api/usage",headers=headers).json()["budget"]["reserved_usd"] == 0


def test_deletion_erases_visitor_data_but_preserves_global_cost_durably(gateway):
    app,client,provider,_=gateway
    headers=login(client)
    result=sample(client,headers)
    session=session_from(app,headers)
    before=app.ledger.snapshot()
    assert before["spent_usd"] > 0
    assert client.delete("/api/session",headers=headers).json() == {"deleted":True}
    assert not (app.tenants/session["id"]).exists()
    assert session["id"] not in app.children
    assert client.get("/api/courses",headers=headers).status_code == 401
    assert app.ledger.snapshot() == before
    reopened=DemoLedger(app.ledger.path,app.ledger.limit)
    assert reopened.snapshot() == before
    second=login(client)
    assert client.get("/api/courses",headers=second).json() == []
    assert client.get(f"/api/courses/{result['course']['id']}",headers=second).status_code == 404


def test_workspace_cannot_be_deleted_during_generation_and_cancel_still_responds(gateway):
    app,client,provider,_=gateway
    headers=login(client)
    _,course=source_course(client,headers)
    course_id=course["id"]
    client.post(f"/api/courses/{course_id}/approve",headers=headers,json={"provider_disclosure_accepted":True})
    provider.release=threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        task=pool.submit(client.post,f"/api/courses/{course_id}/generate",headers=headers,json={"idempotency_key":"active-delete-test"})
        try:
            assert provider.started.wait(3)
            deleted=client.delete("/api/session",headers=headers)
            assert deleted.status_code == 409
            latest=client.get(f"/api/courses/{course_id}/job",headers=headers).json()
            cancelled=client.post(f"/api/jobs/{latest['id']}/cancel",headers=headers)
            assert cancelled.status_code == 200
            assert cancelled.json()["cancel_requested"] is True
        finally:
            provider.release.set()
        assert task.result(timeout=5).status_code == 200
    assert client.delete("/api/session",headers=headers).status_code == 200


def test_ttl_cleanup_and_restart_remove_only_inactive_expired_workspaces(gateway):
    app,client,provider,clock=gateway
    headers=login(client)
    source_course(client,headers,mode="demo")
    session=session_from(app,headers)
    directory=app.tenants/session["id"]
    clock[0]+=25*3600
    assert client.get("/api/courses",headers=headers).status_code == 401
    app.active[session["id"]]=1
    app.cleanup()
    assert directory.exists()
    app.active[session["id"]]=0
    restarted=JudgingApplication(app.settings,provider=provider,clock=lambda:clock[0])
    restarted.cleanup()
    assert not directory.exists()
    with restarted.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_orphan_cleanup_preserves_an_active_workspace(gateway):
    app,_,_,_=gateway
    identifier="a"*32
    directory=app.tenants/identifier
    directory.mkdir()
    (directory/"temporary-source.txt").write_text("Temporary source fixture",encoding="utf-8")
    app.active[identifier]=1
    app.cleanup()
    assert directory.exists()
    app.active[identifier]=0
    app.cleanup()
    assert not directory.exists()


def test_deleted_session_snapshot_cannot_recreate_workspace(gateway,monkeypatch):
    app,client,_,_=gateway
    headers=login(client)
    session=session_from(app,headers)
    original=app.session
    def delete_after_lookup(request):
        found=original(request)
        if found:
            with app.lock:
                assert app.erase(found)
        return found
    monkeypatch.setattr(app,"session",delete_after_lookup)
    assert client.get("/api/courses",headers=headers).status_code == 401
    assert not (app.tenants/session["id"]).exists()


def test_normal_course_and_document_caps_and_hosted_provider_limits(gateway):
    _,client,provider,_=gateway
    headers=login(client)
    document,course=source_course(client,headers,mode="demo")
    for field,value in (("modules",4),("assignments",4),("quizzes",4)):
        assert client.post("/api/courses",headers=headers,json={"document_id":document["id"],"title":"Over limit",
            "mode":"nebius",field:value}).status_code == 422
    assert client.post("/api/courses",headers=headers,json={"document_id":document["id"],"title":"OpenAI local only","mode":"openai"}).status_code == 422
    for index in range(11):
        assert client.post("/api/courses",headers=headers,json={"document_id":document["id"],"title":f"Course {index}","mode":"demo"}).status_code == 200
    assert client.post("/api/courses",headers=headers,json={"document_id":document["id"],"title":"Course thirteen","mode":"demo"}).status_code == 413
    for index in range(4):
        assert client.post("/api/documents",headers=headers,files={"file":(f"source-{index}.txt",
            (f"Original observation {index}. Keep a record of the source observation before watering. "*2).encode(),"text/plain")}).status_code == 200
    assert client.post("/api/documents",headers=headers,files={"file":("sixth.txt",
        b"A sixth independent source observation for the private fixture.","text/plain")}).status_code == 413
    assert provider.calls == []


def test_full_storage_blocks_new_versions_and_still_allows_export_and_deletion(gateway):
    app,client,_,_=gateway
    headers=login(client)
    course=sample(client,headers)["course"]
    directory=app.tenants/session_from(app,headers)["id"]
    with (directory/"storage-limit-fixture.bin").open("wb") as stream:
        stream.seek(33*1024*1024-1)
        stream.write(b"x")
    before=client.get(f"/api/courses/{course['id']}/versions",headers=headers).json()
    response=client.post(f"/api/courses/{course['id']}/approve",headers=headers,json={"provider_disclosure_accepted":True})
    assert response.status_code == 413
    assert client.get(f"/api/courses/{course['id']}/versions",headers=headers).json() == before
    assert client.get(f"/api/courses/{course['id']}/export?format=json",headers=headers).status_code == 200
    assert client.delete("/api/session",headers=headers).status_code == 200


def test_concurrent_course_creation_cannot_race_past_the_course_cap(gateway,monkeypatch):
    app,client,_,_=gateway
    headers=login(client)
    document,_=source_course(client,headers,mode="demo")
    for index in range(10):
        assert client.post("/api/courses",headers=headers,json={"document_id":document["id"],
            "title":f"Existing course {index}","mode":"demo"}).status_code == 200
    service=app.child(session_from(app,headers)).state.service
    original=service.create_course
    def slow_save(options):
        time.sleep(.1)
        return original(options)
    monkeypatch.setattr(service,"create_course",slow_save)
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(client.post,"/api/courses",headers=headers,json={"document_id":document["id"],
            "title":f"Concurrent course {index}","mode":"demo"}) for index in range(2)]
        statuses=sorted(task.result(timeout=5).status_code for task in tasks)
    assert statuses == [200,413]
    assert len(client.get("/api/courses",headers=headers).json()) == 12


def test_aggregate_storage_cap_applies_across_visitors(gateway):
    app,client,provider,_=gateway
    app.settings.max_storage_mib=50
    first=login(client)
    source_course(client,first,mode="demo")
    directory=app.tenants/session_from(app,first)["id"]
    with (directory/"aggregate-storage-fixture.bin").open("wb") as stream:
        stream.seek(30*1024*1024-1)
        stream.write(b"x")
    second=login(client)
    assert client.post("/api/documents/sample",headers=second).status_code == 413
    assert client.get("/api/courses",headers=second).json() == []
    assert client.delete("/api/session",headers=first).status_code == 200
    assert client.post("/api/documents/sample",headers=second).status_code == 200
    assert provider.calls == []


def test_https_cookie_stays_secure_even_if_local_http_option_is_enabled(gateway):
    app,client,_,_=gateway
    app.settings.allow_http=True
    response=client.post("/api/session",json={"access_code":ACCESS_CODE})
    assert response.status_code == 200
    assert "; secure" in response.headers["set-cookie"].lower()


def test_session_capacity_and_missing_provider_key_fail_without_charges(gateway):
    app,client,provider,_=gateway
    app.settings.max_sessions=1
    headers=login(client)
    assert client.post("/api/session",json={"access_code":ACCESS_CODE}).status_code == 503
    provider.key_configured=False
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/live").status_code == 200
    response=client.post("/api/sample-course",headers=headers,json={
        "provider_disclosure_accepted":True,"idempotency_key":"no-configured-provider"})
    assert response.status_code == 400
    assert provider.calls == []
    assert app.ledger.snapshot()["spent_usd"] == app.ledger.snapshot()["reserved_usd"] == 0
    assert client.delete("/api/session",headers=headers).status_code == 200
    assert client.post("/api/session",json={"access_code":ACCESS_CODE}).status_code == 200


def test_sqlite_contexts_close_connections_and_restart_keeps_unknown_cost_reservation(gateway):
    app,_,_,_=gateway
    for connect in (app.connect,app.ledger.connect):
        with connect() as db:
            assert db.execute("SELECT 1").fetchone()[0] == 1
        with pytest.raises(sqlite3.ProgrammingError):
            db.execute("SELECT 1")
    app.ledger.reserve("test-session",NEBIUS_MODEL,"generation",.2)
    restarted=DemoLedger(app.ledger.path,app.ledger.limit)
    assert restarted.snapshot()["reserved_usd"] == .2
    assert restarted.snapshot()["uncertain_calls"] == 1


def test_operator_status_exposes_no_secrets_and_requires_its_own_authentication(gateway):
    app,client,provider,clock=gateway
    assert client.get("/api/operator/status").status_code == 401
    assert client.get("/api/operator/status",headers={"authorization":"Bearer incorrect"}).status_code == 401
    app.settings.credit_expires_at="2026-10-20T12:00:00Z"
    response=client.get("/api/operator/status",headers={"authorization":"Bearer "+OPERATOR_TOKEN})
    assert response.status_code == 200
    assert response.json()["needs_attention"] is True
    assert response.json()["credit_expiry_within_seven_days"] is True
    assert response.json()["provider_balance_verified"] is False
    assert provider.api_key not in response.text and OPERATOR_TOKEN not in response.text
    assert PASSWORD_HASH not in response.text
    clock[0]=datetime(2026,12,17,tzinfo=timezone.utc).timestamp()
    assert client.get("/health/ready").json()["generation_available"] is False
    assert client.get("/api/operator/status",headers={"authorization":"Bearer "+OPERATOR_TOKEN}).json()["needs_attention"] is True
    assert client.get("/api/session").status_code == 503
    assert datetime.fromisoformat(app.settings.expires_at.replace("Z","+00:00")) >= datetime(2026,12,16,8,tzinfo=timezone.utc)


def test_global_concurrency_and_budget_reservations_remain_bounded(tmp_path):
    provider=FakeProvider()
    provider.delay=.05
    ledger=DemoLedger(tmp_path/"ledger.sqlite3",5,concurrency=2)
    payload={"passages":[{"id":"p1","text":"Only the supplied source observation."}],
             "options":{"assignments":0,"quizzes":0,"questions_per_quiz":1}}
    with ThreadPoolExecutor(max_workers=6) as pool:
        tasks=[pool.submit(MeteredProvider(provider,ledger,f"session-{index}").generate,payload) for index in range(6)]
        for task in tasks:
            assert len(task.result(timeout=5)[0].sections) == 5
    assert provider.maximum_in_flight == 2
    assert ledger.snapshot()["reserved_usd"] == 0
    assert ledger.snapshot()["spent_usd"] == cost(UsageCounts(600,240),NEBIUS_PRICING)
    limited=DemoLedger(tmp_path/"bounded.sqlite3",1)
    barrier=threading.Barrier(2)
    def reserve(index):
        barrier.wait(timeout=2)
        try:
            return limited.reserve(f"visitor-{index}",NEBIUS_MODEL,"generation",.6)
        except ProviderCallRejected:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids=list(pool.map(reserve,range(2)))
    assert sum(identifier is not None for identifier in ids) == 1
    assert limited.snapshot()["reserved_usd"] == .6


@pytest.mark.parametrize("failure,expected_spent,uncertain",[
    (ProviderOutputError(UsageCounts(100,40)),cost(UsageCounts(100,40),NEBIUS_PRICING),False),
    (ProviderCallRejected(),0,False),(RuntimeError("private-source-error-fixture"),0,True),
])
def test_global_ledger_accounts_invalid_output_and_unknown_calls_without_source_or_key(tmp_path,failure,expected_spent,uncertain):
    provider=FakeProvider()
    provider.failure=failure
    ledger=DemoLedger(tmp_path/"ledger.sqlite3",5)
    metered=MeteredProvider(provider,ledger,"private-review-visitor")
    with pytest.raises(type(failure)):
        metered.generate({"passages":[{"id":"p1","text":"private-source-error-fixture"}]})
    state=ledger.snapshot()
    assert state["spent_usd"] == expected_spent
    assert bool(state["reserved_usd"]) is uncertain
    assert bool(state["uncertain_calls"]) is uncertain
    assert b"private-source-error-fixture" not in ledger.path.read_bytes()
    assert provider.api_key.encode() not in ledger.path.read_bytes()
    assert len(provider.calls) == 1


def test_cancelled_write_waiter_cannot_take_the_gate_after_cancellation():
    lock=threading.Lock()
    lock.acquire()
    async def cancel_waiter():
        task=asyncio.create_task(acquire_write_gate(lock,timeout=.2))
        await asyncio.sleep(.03)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        lock.release()
        # An abandoned blocking thread could acquire after its awaiter was cancelled.
        await asyncio.sleep(.05)
        assert lock.acquire(blocking=False)
        lock.release()
    asyncio.run(cancel_waiter())


def test_write_gate_timeout_leaves_no_waiter_and_allows_a_later_acquisition():
    lock=threading.Lock()
    lock.acquire()
    async def bounded_wait():
        assert await acquire_write_gate(lock,timeout=.02) is False
        lock.release()
        assert await acquire_write_gate(lock,timeout=.02) is True
        lock.release()
        assert lock.acquire(blocking=False)
        lock.release()
    asyncio.run(bounded_wait())


def test_request_body_deadline_is_total_even_when_chunks_keep_arriving(gateway,monkeypatch):
    app,_,_,_=gateway
    delivered=[]
    clock=[0]
    async def trickle():
        await asyncio.sleep(0)
        clock[0]+=.02
        delivered.append(b"x")
        return {"type":"http.request","body":b"x","more_body":len(delivered) < 4}
    async def bounded_body():
        # Every individual chunk arrives within .05 seconds, but the complete
        # virtual .08-second body exceeds the total. Advancing only this reader's
        # clock makes the regression deterministic without slow network timing.
        with monkeypatch.context() as patch:
            patch.setattr(asyncio,"get_running_loop",lambda:SimpleNamespace(time=lambda:clock[0]))
            with pytest.raises(asyncio.TimeoutError):
                await app.body(trickle,maximum=1024,timeout=.05)
    asyncio.run(bounded_body())
    assert 0 < len(delivered) < 4


@pytest.mark.parametrize("authenticated",[False,True])
def test_body_timeout_returns_safe_408_and_releases_slots_and_visitor_pin(gateway,monkeypatch,authenticated):
    app,client,provider,_=gateway
    headers=login(client) if authenticated else {}
    path="/api/documents" if authenticated else "/api/session"
    original=app.body
    requested_timeouts=[]
    async def short_deadline(receive,maximum,timeout=60):
        requested_timeouts.append(timeout)
        return await original(receive,maximum,timeout=.02)
    monkeypatch.setattr(app,"body",short_deadline)
    messages=[]
    partial="private-unfinished-input-fixture"
    scope={"type":"http","asgi":{"version":"3.0"},"http_version":"1.1","method":"POST",
        "scheme":"https","path":path,"raw_path":path.encode(),"query_string":b"",
        "server":("judge.example",443),"client":("198.51.100.10",1234),
        "headers":[(b"host",b"judge.example"),(b"content-type",b"application/json")]+
                  [(name.encode(),value.encode()) for name,value in headers.items()]}
    async def stalled_request():
        delivered=False
        forever=asyncio.Event()
        async def receive():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {"type":"http.request","body":partial.encode(),"more_body":True}
            await forever.wait()
        async def send(message):
            messages.append(message)
        await asyncio.wait_for(app(scope,receive,send),timeout=1)
    asyncio.run(stalled_request())
    start=next(message for message in messages if message["type"] == "http.response.start")
    body=b"".join(message.get("body",b"") for message in messages if message["type"] == "http.response.body")
    assert start["status"] == 408
    assert dict(start["headers"])[b"connection"] == b"close"
    assert partial.encode() not in body and provider.api_key.encode() not in body
    assert requested_timeouts == [60 if authenticated else 10]
    assert all(count == 0 for count in app.active.values())
    assert not app.write_gate.locked()
    held=0
    try:
        while app.web_slots.acquire(blocking=False):
            held+=1
        assert held == 16
    finally:
        for _ in range(held):
            app.web_slots.release()
    assert client.get("/api/session",headers=headers).status_code == 200
    assert provider.calls == []


def test_hosted_pdf_stream_bound_rejects_compressed_expansion_and_restores_local_limits(gateway,tmp_path):
    app,client,provider,_=gateway
    headers=login(client)
    ordinary=SAMPLE_PATH.with_suffix(".pdf").read_bytes()
    uploaded=client.post("/api/documents",headers=headers,files={"file":("ordinary.pdf",ordinary,"application/pdf")})
    assert uploaded.status_code == 200
    assert uploaded.json()["passages"]
    service=app.child(session_from(app,headers)).state.service
    before=get_configuration()
    writer=PdfWriter()
    writer.append_pages_from_reader(PdfReader(io.BytesIO(ordinary)))
    first=writer.pages[0]
    contents=DecodedStreamObject()
    # Compressible, harmless PDF whitespace exceeds the hosted eight-MiB stream
    # allowance while preserving the original readable sample's visible text.
    contents.set_data(b" "*(9*1024*1024)+first.get_contents().get_data())
    first[NameObject("/Contents")]=writer._add_object(contents.flate_encode())
    output=io.BytesIO()
    writer.write(output)
    compressed=output.getvalue()
    assert len(compressed) < 1024*1024
    with pytest.raises(ExtractionError,match="could not be read"):
        service.document(compressed,"expanded-stream.pdf")
    assert get_configuration() is before
    local=Service(tmp_path/"local-control",0)
    accepted=local.document(compressed,"expanded-stream.pdf")
    assert accepted["passages"]
    assert get_configuration() is before
    assert {p["text"] for p in uploaded.json()["passages"]} == {p["text"] for p in accepted["passages"]}
    assert provider.calls == []
