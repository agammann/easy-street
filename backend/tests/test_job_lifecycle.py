from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import Event
import os
import subprocess
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from backend.demo import demo_course
from backend.extraction import SAMPLE_PATH
from backend.main import create_app
from backend.models import CourseInput, GenerateInput, Verification
from backend.provider import UsageCounts
from backend.service import Service


class SampleProvider:
    def __init__(self):
        self.calls = []
        self.document = None
    def generate(self,payload):
        self.calls.append("generate")
        return demo_course(self.document,payload["options"]["questions_per_quiz"])[0],UsageCounts(1,1)
    def verify(self,payload):
        self.calls.append("verify")
        return Verification(results=[{"section_id":s["id"],"status":"supported","reason":"Original sample."} for s in payload["sections"]]),UsageCounts(1,1)


def approved_course(service,provider):
    provider.document = service.document(SAMPLE_PATH.read_bytes(),"sample.txt")
    course = service.create_course(CourseInput(document_id=provider.document["id"],title="Garden",mode="openai",questions_per_quiz=1))
    course["outline_approved"] = True
    service.store.put_course(course)
    return course


def generate(service,course,key):
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key=key))
    service.run(job["id"])
    assert service.store.get("jobs",job["id"])["status"] == "complete"
    return job


def test_cached_course_needs_no_remaining_budget_or_configured_key(tmp_path):
    provider = SampleProvider()
    service = Service(tmp_path,1,provider)
    course = approved_course(service,provider)
    generate(service,course,"first-cache-run")
    calls = list(provider.calls)
    service.store.budget_limit = service.store.budget()["spent_usd"]
    service.key_configured = False
    duplicate = approved_course(service,provider)
    assert service.estimate(duplicate)["estimated_max_usd"] == 0
    generate(service,duplicate,"second-cache-run")
    assert provider.calls == calls
    assert service.store.budget()["reserved_usd"] == 0


def test_cancellation_cannot_be_lost_between_stage_read_and_write(tmp_path,monkeypatch):
    provider = SampleProvider()
    service = Service(tmp_path,1,provider)
    course = approved_course(service,provider)
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="cancel-race-test"))
    original_get = service.store.get
    raced = False
    def get_with_concurrent_cancellation(table,id):
        nonlocal raced
        snapshot = original_get(table,id)
        if table == "jobs" and id == job["id"] and not raced:
            raced = True
            service.store.put_job({**snapshot,"cancel_requested":True})
        return snapshot
    monkeypatch.setattr(service.store,"get",get_with_concurrent_cancellation)
    service.job_stage(job,"preparing")
    assert original_get("jobs",job["id"])["cancel_requested"] is True


def test_cancel_during_preparation_prevents_new_provider_call(tmp_path,monkeypatch):
    provider = SampleProvider()
    service = Service(tmp_path,1,provider)
    course = approved_course(service,provider)
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="cancel-before-dispatch"))
    original_budget_check = service.store.ensure_call_budget
    def cancel_before_dispatch(id,maximum):
        original_budget_check(id,maximum)
        saved = service.store.get("jobs",id)
        saved["cancel_requested"] = True
        service.store.put_job(saved)
    monkeypatch.setattr(service.store,"ensure_call_budget",cancel_before_dispatch)
    service.run(job["id"])
    assert provider.calls == []
    assert service.store.get("jobs",job["id"])["status"] == "cancelled"
    assert service.store.budget()["reserved_usd"] == 0


def test_failed_regeneration_finalization_does_not_overwrite_new_manual_edit(tmp_path,monkeypatch):
    provider = SampleProvider()
    app = create_app(tmp_path,provider=provider,budget_limit=1)
    service = app.state.service
    client = TestClient(app,base_url="http://localhost")
    course = approved_course(service,provider)
    generate(service,course,"initial-edit-race")
    # This provider deliberately returns a whole course for targeted regeneration.
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="failing-regeneration",section_id="notes"))
    status_written,finish_cleanup = Event(),Event()
    original_put = service.store.put_job
    def pause_after_failed_status(saved,release=False):
        original_put(saved,release)
        if saved["id"] == job["id"] and saved["status"] == "failed":
            status_written.set()
            assert finish_cleanup.wait(5)
    monkeypatch.setattr(service.store,"put_job",pause_after_failed_status)
    with ThreadPoolExecutor(max_workers=2) as pool:
        running = pool.submit(service.run,job["id"])
        assert status_written.wait(5)
        edited = pool.submit(client.patch,f"/api/courses/{course['id']}/sections/announcement",json={"body":"Preserve this new manual edit."})
        try:
            # Before the fix the request completes inside the unsafe cleanup window.
            edited.result(timeout=0.2)
        except FutureTimeout:
            pass
        finally:
            finish_cleanup.set()
        running.result(timeout=5)
        assert edited.result(timeout=5).status_code == 200
    saved = service.store.get("courses",course["id"])
    assert next(s for s in saved["sections"] if s["id"] == "announcement")["body"] == "Preserve this new manual edit."


def test_latest_job_is_discoverable_after_restart_without_private_outputs(tmp_path):
    provider = SampleProvider()
    app = create_app(tmp_path,provider=provider,budget_limit=1)
    service = app.state.service
    course = approved_course(service,provider)
    client = TestClient(app,base_url="http://localhost")
    assert client.get(f"/api/courses/{course['id']}/job").json() is None
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="discover-restart-job"))
    job["generated"] = {"private":"provider output"}
    job["verification"] = {"private":"provider review"}
    service.store.put_job(job)
    restarted = TestClient(create_app(tmp_path,provider=provider,budget_limit=1),base_url="http://localhost")
    found = restarted.get(f"/api/courses/{course['id']}/job")
    assert found.status_code == 200
    assert found.json()["id"] == job["id"] and found.json()["status"] == "interrupted"
    assert "generated" not in found.json() and "verification" not in found.json()
    assert restarted.get("/api/courses/missing/job").status_code == 404


def test_importing_factory_does_not_recover_jobs_in_default_database(tmp_path):
    provider = SampleProvider()
    service = Service(tmp_path,1,provider)
    course = approved_course(service,provider)
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="factory-import-live-job"))
    job.update(status="running",stage="generation_in_flight")
    service.store.put_job(job)
    before = service.store.get("jobs",job["id"])
    env = {**os.environ,"EASY_STREET_DATA_DIR":str(tmp_path),"PYTHON_DOTENV_DISABLED":"1"}
    subprocess.run([sys.executable,"-c","import backend.main; assert not hasattr(backend.main, 'app')"],
                   cwd=Path(__file__).resolve().parents[2],env=env,check=True,capture_output=True,text=True,timeout=15)
    assert service.store.get("jobs",job["id"]) == before
    assert service.store.get("courses",course["id"])["status"] == "generating"
