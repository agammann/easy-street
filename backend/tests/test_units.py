import io
import json
import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from backend.extraction import extract, ExtractionError, SAMPLE_PATH, select_passages
from backend.demo import demo_course
from backend.grounding import ground_sections, validate_structure
from backend.models import GeneratedCourse, Verification, CourseInput, GenerateInput
from backend.service import Service
from backend.provider import estimate, UsageCounts


def original():
    return extract(SAMPLE_PATH.read_bytes(),"sample.txt")


def pdf_bytes():
    writer = PdfWriter()
    page = writer.add_blank_page(width=612,height=792)
    font = DictionaryObject({NameObject("/Type"):NameObject("/Font"),NameObject("/Subtype"):NameObject("/Type1"),NameObject("/BaseFont"):NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):DictionaryObject({NameObject("/F1"):font})})
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 30 750 Td (A small original chapter about garden soil. Check the soil before watering.) Tj 0 -20 Td (If soil feels dry below the surface, add water slowly so it can soak in.) Tj 0 -20 Td (Keep a record of observations and actions for each container.) Tj ET")
    page[NameObject("/Contents")] = content
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_pdf_extraction_stable_real_page_references():
    a = extract(pdf_bytes(),"garden.pdf")
    b = extract(pdf_bytes(),"renamed.pdf")
    assert a["id"] == b["id"]
    assert a["passages"][0]["page"] == 1
    assert "-p0001-b0001" in a["passages"][0]["id"]
    assert "garden soil" in a["passages"][0]["text"]
    assert any("images, tables, or equations" in w for w in a["warnings"])


def test_text_has_paragraphs_never_invented_pages():
    value = original()
    assert len(value["passages"]) == 6
    assert all(p["page"] is None for p in value["passages"])
    assert value["passages"][1]["location"] == "Paragraph 2"


@pytest.mark.parametrize("data,name",[(b"no PDF", "bad.pdf"),(b"\xff"*200,"bad.txt"),(b"x"*200,"bad.docx"),(b"too little","bad.txt")])
def test_bad_uploads_rejected(data,name):
    with pytest.raises(ExtractionError):
        extract(data,name)


def test_blank_scanned_pdf_requires_local_ocr():
    writer = PdfWriter()
    writer.add_blank_page(width=612,height=792)
    data = io.BytesIO()
    writer.write(data)
    with pytest.raises(ExtractionError,match="Too little readable"):
        extract(data.getvalue(),"scan.pdf")


@pytest.mark.parametrize("questions",[1,2,3,4,5])
def test_demo_question_counts_and_exact_evidence(questions):
    doc = original()
    generated, verification = demo_course(doc,questions)
    validate_structure(generated,questions)
    sections = ground_sections(generated,doc["passages"],verification)
    assert len([s for s in sections if s["kind"] == "quiz"]) == questions
    assert all(s["support_status"] != "needs_review" for s in sections)


def test_broken_citations_and_missing_verification_are_flags():
    doc = original()
    generated, verification = demo_course(doc,1)
    generated.sections[1].evidence[0].quote = "A quotation never contained in this chapter."
    generated.sections[2].evidence[0].passage_id = "invented-p9999"
    verification.results = verification.results[1:]
    sections = ground_sections(generated,doc["passages"],verification)
    assert "missing" in sections[0]["review_notes"][0]
    assert any("exact match" in note for note in sections[1]["review_notes"])
    assert any("does not resolve" in note for note in sections[2]["review_notes"])


def test_valid_citation_does_not_override_unsupported_verifier():
    doc = original()
    generated, verification = demo_course(doc,1)
    verification.results[-1].status = "conflicting"
    verification.results[-1].reason = "Two passages disagree."
    sections = ground_sections(generated,doc["passages"],verification)
    assert sections[-1]["support_status"] == "needs_review"
    assert "conflicting" in sections[-1]["review_notes"][0]


def test_counts_duplicates_and_wrong_regeneration_rejected():
    generated, _ = demo_course(original(),1)
    with pytest.raises(ValueError,match="counts"):
        validate_structure(generated,2)
    generated.sections[-1].id = generated.sections[0].id
    with pytest.raises(ValueError,match="duplicate"):
        validate_structure(generated,1)
    one = GeneratedCourse(sections=[generated.sections[0]])
    with pytest.raises(ValueError,match="preserve"):
        validate_structure(one,1,{"id":"other","kind":"notes"})


def test_schema_rejects_extra_fields_and_non_quiz_answers():
    generated, _ = demo_course(original(),1)
    value = generated.model_dump()
    value["sections"][0]["secret"] = "untrusted"
    with pytest.raises(ValidationError):
        GeneratedCourse.model_validate(value)
    generated.sections[0].answer = "stray answer"
    with pytest.raises(ValueError,match="Answer-key"):
        validate_structure(generated,1)


def test_hash_cache_original_storage_and_restart(tmp_path):
    svc = Service(tmp_path,1)
    a = svc.document(SAMPLE_PATH.read_bytes(),"sample.txt")
    b = svc.document(SAMPLE_PATH.read_bytes(),"other.txt")
    assert b["cached"] and a["id"] == b["id"]
    assert len(list((tmp_path / "originals").iterdir())) == 1
    restarted = Service(tmp_path,1)
    assert restarted.store.get("documents",a["id"])["passages"] == a["passages"]


def test_restart_safe_resume_and_uncertain_request_never_retried(tmp_path):
    svc = Service(tmp_path,1)
    doc = svc.document(SAMPLE_PATH.read_bytes(),"sample.txt")
    course = svc.create_course(CourseInput(document_id=doc["id"],title="Garden",mode="demo"))
    course["outline_approved"] = True
    svc.store.put_course(course)
    job, _ = svc.submit(course["id"],GenerateInput(idempotency_key="recovery-001"))
    restarted = Service(tmp_path,1)
    assert restarted.store.get("jobs",job["id"])["status"] == "interrupted"
    uncertain = restarted.store.get("jobs",job["id"])
    uncertain.update(status="running",stage="generation_in_flight")
    restarted.store.put_job(uncertain)
    final = Service(tmp_path,1)
    assert final.store.get("jobs",job["id"])["status"] == "uncertain"
    final.run(job["id"])
    assert final.store.get("jobs",job["id"])["status"] == "uncertain"


def test_budget_reservation_includes_verification():
    result = estimate({"passages":[{"text":"Small source"}]})
    assert result["verification_included"]
    assert result["estimated_max_usd"] > 0.10
    assert result["output_tokens_limit"] == 11500


def test_source_scope_warning_and_selected_ids(tmp_path):
    svc = Service(tmp_path,1)
    doc = svc.document(("Long heading\n" + "Many source words. "*400 + "\n\n") .encode()*6,"chapter.txt")
    course = svc.create_course(CourseInput(document_id=doc["id"],title="Source coverage"))
    assert len(course["outline"]["selected_passage_ids"]) < len(doc["passages"])
    assert any("not covered" in w for w in course["outline"]["warnings"])


@pytest.mark.parametrize("checkpoint",["generation_received","verification_received"])
def test_restart_reuses_completed_provider_checkpoints(tmp_path,checkpoint):
    class RecordingProvider:
        generate_calls = 0
        verify_calls = 0
        def generate(self,payload):
            self.generate_calls += 1
            raise AssertionError("Completed generation must not be repeated")
        def verify(self,payload):
            self.verify_calls += 1
            return demo_course(original(),1)[1], UsageCounts(50,50)
    provider = RecordingProvider()
    svc = Service(tmp_path,10,provider)
    doc = svc.document(SAMPLE_PATH.read_bytes(),"sample.txt")
    course = svc.create_course(CourseInput(document_id=doc["id"],title="Garden",mode="openai",questions_per_quiz=1))
    course["outline_approved"] = True
    svc.store.put_course(course)
    job, _ = svc.submit(course["id"],GenerateInput(idempotency_key="checkpoint-001"))
    generated, verified = demo_course(doc,1)
    job.update(status="running",stage=checkpoint,generated=generated.model_dump())
    if checkpoint == "verification_received":
        job["verification"] = verified.model_dump()
    svc.store.put_job(job)
    restarted = Service(tmp_path,10,provider)
    saved = restarted.store.get("jobs",job["id"])
    assert saved["status"] == "interrupted"
    saved["status"] = "queued"
    restarted.store.put_job(saved)
    restarted.run(saved["id"])
    result = restarted.store.get("jobs",saved["id"])
    assert result["status"] == "complete"
    assert provider.generate_calls == 0
    assert provider.verify_calls == (1 if checkpoint == "generation_received" else 0)
    assert restarted.store.budget()["reserved_usd"] == 0
