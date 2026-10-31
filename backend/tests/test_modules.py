from collections import Counter
import copy
import hashlib
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from backend.demo import demo_module
from backend.extraction import SAMPLE_PATH
from backend.exports import export_course
from backend.main import create_app
from backend.models import CourseInput, GenerateInput, Verification
from backend.provider import MODEL, UsageCounts
from backend.service import Service
from backend.store import Store


class SampleProvider:
    def __init__(self):
        self.document = None
        self.generated = []
        self.verified = []
    def generate(self,payload):
        self.generated.append(copy.deepcopy(payload))
        generated,_ = demo_module(self.document,payload)
        return generated,UsageCounts(10,10)
    def verify(self,payload):
        self.verified.append(copy.deepcopy(payload))
        return Verification(results=[{"section_id":s["id"],"status":"supported","reason":"Deterministic fixture."} for s in payload["sections"]]),UsageCounts(10,10)


def setup_course(tmp_path,modules=3,assignments=3,quizzes=3,questions=2,mode="openai"):
    provider = SampleProvider()
    service = Service(tmp_path,10,provider)
    provider.document = service.document(SAMPLE_PATH.read_bytes(),"chapter.txt")
    course = service.create_course(CourseInput(document_id=provider.document["id"],title="A complete garden course",
        modules=modules,assignments=assignments,quizzes=quizzes,questions_per_quiz=questions,mode=mode))
    course["outline_approved"] = True
    service.store.put_course(course)
    return service,provider,course


def generate(service,course,key="module-generation"):
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key=key))
    service.run(job["id"])
    assert service.store.get("jobs",job["id"])["status"] == "complete"
    return service.store.get("courses",course["id"]),service.store.get("jobs",job["id"])


@pytest.mark.parametrize("modules,assignments,quizzes,questions",[(3,3,3,2),(3,6,6,5),(6,0,0,1),(1,0,2,3)])
def test_module_counts_membership_sources_and_course_export(tmp_path,modules,assignments,quizzes,questions):
    service,provider,course = setup_course(tmp_path,modules,assignments,quizzes,questions)
    saved,job = generate(service,course)
    counts = Counter(s["kind"] for s in saved["sections"])
    assert counts["assignment"] == counts["rubric"] == assignments
    assert counts["quiz"] == quizzes * questions
    assert all(counts[kind] == modules for kind in ("objectives","introduction","readings","notes","announcement"))
    assert len({s["id"] for s in saved["sections"]}) == len(saved["sections"])
    assert [s["order"] for s in saved["sections"]] == list(range(len(saved["sections"])))
    assert job["completed_modules"] == job["total_modules"] == modules
    assert len(provider.generated) == len(provider.verified) == modules
    for module in saved["outline"]["modules"]:
        sections = [s for s in saved["sections"] if s["module_id"] == module["id"]]
        assert all(ev["passage_id"] in module["selected_passage_ids"] for section in sections for ev in section["evidence"])
        assert len({s["assessment_id"] for s in sections if s["kind"] == "quiz"}) == module["quizzes"]
    learner,_,_ = export_course(saved,"html",provider.document)
    answers,_,_ = export_course(saved,"answers",provider.document)
    assert "Proposed syllabus" in learner and "Course objectives" in learner
    assert all(module["title"] in learner for module in saved["outline"]["modules"])
    assert "<h3>Answer</h3>" not in learner
    assert ("<h3>Answer</h3>" in answers) == bool(quizzes)


def test_source_plan_reaches_end_of_long_document_and_explicitly_warns(tmp_path):
    service = Service(tmp_path,1)
    source = "\n\n".join(f"Topic {i}\n"+f"Distinct source statement {i}. "*110 for i in range(35))
    document = service.document(source.encode(),"long.txt")
    course = service.create_course(CourseInput(document_id=document["id"],title="Distributed coverage",modules=3))
    selected = course["outline"]["selected_passage_ids"]
    assert document["passages"][0]["id"] in selected
    assert document["passages"][-1]["id"] in selected
    assert len(selected) < len(document["passages"])
    assert any("not covered" in warning for warning in course["outline"]["warnings"])
    lookup = {p["id"]:p for p in document["passages"]}
    assert all(sum(len(lookup[id]["text"]) for id in module["selected_passage_ids"]) <= 24000 for module in course["outline"]["modules"])


@pytest.mark.parametrize("paragraphs", [["A."] * 2600, ["A."] * 470 + ["A" * 78 + ". B."] * 30])
def test_proposed_plan_fits_actual_catalog_with_many_short_passages(tmp_path, paragraphs):
    provider = SampleProvider()
    service = Service(tmp_path, 1, provider)
    document = service.document("\n\n".join(paragraphs).encode(), "short-paragraphs.txt")
    course = service.create_course(CourseInput(document_id=document["id"], title="Short paragraphs"))
    selected = course["outline"]["selected_passage_ids"]
    assert document["passages"][0]["id"] in selected and document["passages"][-1]["id"] in selected
    assert len(selected) < len(document["passages"])
    assert any("not covered" in warning for warning in course["outline"]["warnings"])
    assert service.estimate(course)["provider_calls_max"] == 2
    assert provider.generated == provider.verified == []


def test_outline_edit_refreshes_review_summary_without_advancing_workflow(tmp_path):
    provider = SampleProvider()
    app = create_app(tmp_path, provider=provider)
    client = TestClient(app, base_url="http://localhost")
    document = client.post("/api/documents/sample").json()
    course = client.post("/api/courses", json={"document_id":document["id"], "title":"Review flags", "mode":"demo", "modules":2}).json()
    path = f"/api/courses/{course['id']}"
    client.post(path + "/approve", json={"provider_disclosure_accepted":True})
    client.post(path + "/generate", json={"idempotency_key":"outline-review-flags"})
    assert client.get(path).json()["review_flags"] == []
    response = client.patch(path + "/outline", json={"title":"Revised objectives"})
    assert response.status_code == 200
    revised = response.json()
    assert revised["status"] == "outline" and not revised["outline_approved"]
    assert len(revised["review_flags"]) == len(revised["sections"])
    assert all(section["support_status"] == "needs_review" for section in revised["sections"])
    assert client.get(path).json()["review_flags"] == revised["review_flags"]


def test_demo_prefers_substantive_excerpts_and_keeps_full_reading_scope(tmp_path):
    service, provider, course = setup_course(tmp_path, modules=2, assignments=2, quizzes=2, mode="demo")
    saved, _ = generate(service, course)
    first_module = saved["outline"]["modules"][0]
    heading_id = provider.document["passages"][0]["id"]
    assert heading_id in first_module["selected_passage_ids"]
    sections = [section for section in saved["sections"] if section["module_id"] == first_module["id"]]
    study = [section for section in sections if section["kind"] in ("introduction", "notes", "assignment", "quiz")]
    assert all(section["evidence"] and all(evidence["passage_id"] != heading_id for evidence in section["evidence"]) for section in study)
    readings = next(section for section in sections if section["kind"] == "readings")
    assert {evidence["passage_id"] for evidence in readings["evidence"]} == set(first_module["selected_passage_ids"])
    assert provider.generated == provider.verified == []


@pytest.mark.parametrize("mode", ["demo", "openai"])
def test_demo_revision_invalidates_only_old_demo_cache(tmp_path, mode):
    service, _, course = setup_course(tmp_path, modules=1, assignments=1, quizzes=1, mode=mode)
    payload = service.payload(course)
    previous_key = hashlib.sha256(json.dumps({"payload":payload,"model":MODEL,"mode":mode},sort_keys=True).encode()).hexdigest()
    service.store.cache_put(previous_key, {"old_cache_entry":True})
    assert service.estimate(course)["modules"][0]["cached"] == (mode == "openai")


def test_outline_distribution_and_sources_are_validated_before_approval(tmp_path):
    service,provider,course = setup_course(tmp_path)
    original = copy.deepcopy(course)
    for field,value in (("selected_passage_ids",[]),("selected_passage_ids",["unknown"]),("assignments",2)):
        changed = copy.deepcopy(original["outline"]["modules"])
        changed[0][field] = value
        with pytest.raises(ValueError):
            service.edit_outline(copy.deepcopy(original),{"modules":changed})
    changed = copy.deepcopy(original["outline"]["modules"])
    changed[0]["assignments"],changed[1]["assignments"] = 2,0
    edited = service.edit_outline(copy.deepcopy(original),{"modules":changed})
    assert edited["outline"]["distribution"][0]["assignments"] == 2
    assert provider.generated == []


class ProcessStopped(BaseException):
    pass


@pytest.mark.parametrize("stage",["generation_received","verification_received","module_complete"])
def test_restart_reuses_each_module_checkpoint_without_repeating_calls(tmp_path,monkeypatch,stage):
    service,provider,course = setup_course(tmp_path)
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="module-checkpoint"))
    original = service.job_stage
    stopped = False
    def stop_after_checkpoint(job,next_stage):
        nonlocal stopped
        original(job,next_stage)
        if next_stage == stage and not stopped:
            stopped = True
            raise ProcessStopped()
    monkeypatch.setattr(service,"job_stage",stop_after_checkpoint)
    with pytest.raises(ProcessStopped):
        service.run(job["id"])
    restarted = Service(tmp_path,10,provider)
    saved = restarted.store.get("jobs",job["id"])
    assert saved["status"] == "interrupted"
    saved["status"] = "queued"
    restarted.store.put_job(saved)
    restarted.run(saved["id"])
    result = restarted.store.get("jobs",saved["id"])
    assert result["status"] == "complete"
    assert len(provider.generated) == len(provider.verified) == 3
    assert restarted.store.budget()["reserved_usd"] == 0
    assert len(restarted.store.get("courses",course["id"])["sections"]) == 27


def test_cancellation_keeps_completed_modules_and_new_request_only_finishes_remaining(tmp_path,monkeypatch):
    service,provider,course = setup_course(tmp_path)
    original = service.job_stage
    def cancel_after_first_module(job,stage):
        original(job,stage)
        if stage == "module_complete" and job["completed_modules"] == 1:
            job["cancel_requested"] = True
            service.store.put_job(job)
    monkeypatch.setattr(service,"job_stage",cancel_after_first_module)
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="partial-course-cancel"))
    service.run(job["id"])
    assert service.store.get("jobs",job["id"])["status"] == "cancelled"
    partial = service.store.get("courses",course["id"])
    assert partial["generated_module_ids"] == ["module-1"]
    before = copy.deepcopy(partial["sections"])
    monkeypatch.setattr(service,"job_stage",original)
    saved,_ = generate(service,partial,"finish-partial-course")
    assert saved["sections"][:len(before)] == before
    assert [p["module"]["id"] for p in provider.generated] == ["module-1","module-2","module-3"]


def test_module_cache_reuses_all_modules_without_key_or_remaining_budget(tmp_path):
    service,provider,course = setup_course(tmp_path)
    saved,_ = generate(service,course)
    copied = service.create_course(CourseInput(document_id=course["document_id"],title=course["title"],modules=3,assignments=3,quizzes=3,questions_per_quiz=2))
    copied["outline_approved"] = True
    service.store.put_course(copied)
    service.key_configured = False
    service.store.budget_limit = service.store.budget()["spent_usd"]
    estimate = service.estimate(copied)
    assert estimate["estimated_max_usd"] == estimate["provider_calls_max"] == 0
    duplicate,_ = generate(service,copied,"cached-three-modules")
    assert len(provider.generated) == len(provider.verified) == 3
    assert duplicate["sections"] == saved["sections"]


def test_target_regeneration_only_uses_its_module_and_preserves_other_edits(tmp_path):
    service,provider,course = setup_course(tmp_path)
    saved,_ = generate(service,course)
    target = next(s for s in saved["sections"] if s["module_id"] == "module-2" and s["kind"] == "notes")
    unrelated = [copy.deepcopy(s) for s in saved["sections"] if s["module_id"] != "module-2"]
    job,_ = service.submit(course["id"],GenerateInput(idempotency_key="module-two-notes",section_id=target["id"]))
    service.run(job["id"])
    assert service.store.get("jobs",job["id"])["status"] == "complete"
    result = service.store.get("courses",course["id"])
    assert [s for s in result["sections"] if s["module_id"] != "module-2"] == unrelated
    module = saved["outline"]["modules"][1]
    assert set(p["id"] for p in provider.generated[-1]["passages"]) <= set(module["selected_passage_ids"])
    assert {p["id"] for p in provider.verified[-1]["passages"]} == set(module["selected_passage_ids"])


def test_regeneration_payload_omits_saved_section_content(tmp_path):
    service, provider, course = setup_course(tmp_path, modules=1, assignments=1, quizzes=1)
    saved, _ = generate(service, course)
    target = next(s for s in saved["sections"] if s["kind"] == "quiz")
    marker = "SYNTHETIC_PRIVATE_MANUAL_ONLY"
    target.update(title=marker + " title", body=marker + " body", answer=marker + " answer",
                  explanation=marker + " explanation", review_notes=[marker + " review"])
    target["evidence"][0]["quote"] = marker + " local evidence quote"
    target["extra_local_metadata"] = marker + " arbitrary metadata"
    service.store.put_course(saved)
    payload = service.payload(saved, target["id"])
    assert payload["target_section"] == {"id": target["id"], "kind": "quiz"}
    assert marker not in json.dumps(payload)
    assert payload["passages"]
    cache_key = service.cache_key(saved, payload)
    target["body"] = marker + " a different local edit"
    changed_key = service.cache_key(saved, service.payload(saved, target["id"]))
    assert changed_key != cache_key
    target["body"] = marker + " another local edit"
    assert service.cache_key(saved, service.payload(saved, target["id"])) not in (cache_key, changed_key)


def test_regeneration_cache_changes_after_a_saved_edit(tmp_path):
    service, provider, course = setup_course(tmp_path, modules=1, assignments=1, quizzes=1)
    saved, _ = generate(service, course)
    target = next(s for s in saved["sections"] if s["kind"] == "quiz")
    job, _ = service.submit(saved["id"], GenerateInput(idempotency_key="regenerate-first", section_id=target["id"]))
    service.run(job["id"])
    assert service.store.get("jobs", job["id"])["status"] == "complete"
    saved = service.store.get("courses", saved["id"])
    target = next(s for s in saved["sections"] if s["id"] == target["id"])
    marker = "SYNTHETIC_PRIVATE_AFTER_REGENERATION"
    target["body"] = marker
    service.store.put_course(saved)
    local_digest = hashlib.sha256(json.dumps(target,sort_keys=True).encode()).hexdigest()
    estimate = service.estimate(saved, target["id"])
    assert estimate["cached"] is False
    assert local_digest not in json.dumps(estimate)
    job, _ = service.submit(saved["id"], GenerateInput(idempotency_key="regenerate-after-edit", section_id=target["id"]))
    service.run(job["id"])
    assert service.store.get("jobs", job["id"])["status"] == "complete"
    assert len(provider.generated) == 3
    assert marker not in json.dumps(provider.generated[-1])
    assert local_digest not in json.dumps(provider.generated[-1])
    assert local_digest not in json.dumps(provider.verified[-1])


def test_public_module_job_does_not_expose_saved_provider_outputs(tmp_path):
    app = create_app(tmp_path,provider=SampleProvider(),budget_limit=10)
    client = TestClient(app,base_url="http://localhost")
    document = client.post("/api/documents/sample").json()
    course = client.post("/api/courses",json={"document_id":document["id"],"title":"Three modules","modules":3,"mode":"demo"}).json()
    client.post(f"/api/courses/{course['id']}/approve",json={"provider_disclosure_accepted":True})
    job = client.post(f"/api/courses/{course['id']}/generate",json={"idempotency_key":"public-module-progress"}).json()
    public = client.get(f"/api/jobs/{job['id']}").json()
    assert public["completed_modules"] == 3
    assert "module_results" not in public


def test_document_digest_migration_preserves_rows_and_allows_ocr_variants(tmp_path):
    path = tmp_path / "old.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE documents(id TEXT PRIMARY KEY, sha256 TEXT UNIQUE, data TEXT NOT NULL)")
        db.execute("INSERT INTO documents VALUES ('original','digest','{\"id\":\"original\"}')")
    store = Store(path,1)
    store.put_document({"id":"ocr-variant","sha256":"digest"})
    assert store.get("documents","original") == {"id":"original"}
    assert store.get("documents","ocr-variant")["sha256"] == "digest"
