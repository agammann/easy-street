import pytest
from backend.demo import demo_course
from backend.extraction import extract, SAMPLE_PATH
from backend.exports import export_course
from backend.grounding import ground_sections, proposal_title
from backend.models import GeneratedCourse, Verification


def grounded_quote(quote):
    document = extract(SAMPLE_PATH.with_suffix(".pdf").read_bytes(), "chapter.pdf")
    passage = document["passages"][0]
    generated = GeneratedCourse(sections=[{
        "id": "quiz-1", "kind": "quiz", "title": "Question", "body": "What does the source say?",
        "answer": "Review the cited passage.", "explanation": "The passage contains the answer.",
        "evidence": [{"passage_id": passage["id"], "quote": quote}],
    }])
    verification = Verification(results=[{"section_id": "quiz-1", "status": "supported", "reason": "Supported."}])
    return ground_sections(generated, document["passages"], verification)[0], passage["text"]


@pytest.mark.parametrize("quote", [
    "Push a finger about two centimeters into the soil. If the soil feels dry at that depth, the container needs water.",
    "Apply water slowly near the soil surface. Slow watering gives water time to soak into the soil rather than run over the edge of the container.",
])
def test_real_pdf_line_wrapped_quotes_are_stored_as_exact_original_spans(quote):
    section, original = grounded_quote(quote)
    saved_quote = section["evidence"][0]["quote"]
    assert quote not in original  # Regression from the first real provider run.
    assert "\n" in saved_quote
    assert saved_quote in original
    assert " ".join(saved_quote.split()) == quote
    assert section["support_status"] == "supported"
    assert section["review_notes"] == []


@pytest.mark.parametrize("quote", [
    "Push a finger about two centimeters into the soil... the container needs water.",
    "Push a finger about two centimeters into the soil… the container needs water.",
    "Push a finger about three centimeters into the soil.",
    "Push a finger about two centimeters into the soil!",
])
def test_whitespace_resolution_never_accepts_omissions_or_changed_words_and_punctuation(quote):
    section, _ = grounded_quote(quote)
    assert section["support_status"] == "needs_review"
    assert section["evidence"][0]["quote"] == quote
    assert any("not an exact match" in note for note in section["review_notes"])


def test_proposal_titles_remain_explicit_when_evidence_needs_review_and_in_exports():
    document = extract(SAMPLE_PATH.read_bytes(), "chapter.txt")
    generated, verification = demo_course(document, 1)
    proposal_kinds = {"objectives", "announcement", "assignment", "rubric"}
    for section in generated.sections:
        if section.kind in proposal_kinds:
            section.title = f"Unlabeled {section.kind}"
    # A missing verifier result must not remove the independent proposal identification.
    sections = ground_sections(generated, document["passages"], Verification(results=[]))
    for section in sections:
        if section["kind"] in proposal_kinds:
            assert section["title"].startswith("Proposed · ")
            assert section["support_status"] == "needs_review"
            assert proposal_title(section["kind"], section["title"]) == section["title"]
            # Older stored courses also get an explicit label when exported.
            section["title"] = f"Unlabeled {section['kind']}"
    course = {"title": "Garden", "mode": "openai", "sections": sections}
    exported, _, _ = export_course(course, "html", document)
    for kind in proposal_kinds:
        assert f"Proposed · Unlabeled {kind}" in exported
