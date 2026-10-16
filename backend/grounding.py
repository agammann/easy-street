from collections import Counter
from .models import GeneratedCourse, Verification

PROPOSALS = {"objectives", "announcement", "rubric"}


def validate_structure(generated: GeneratedCourse, questions: int, target: dict | None = None):
    ids = [s.id for s in generated.sections]
    if len(ids) != len(set(ids)):
        raise ValueError("Provider returned duplicate section identifiers.")
    if target:
        if len(generated.sections) != 1 or generated.sections[0].id != target["id"] or generated.sections[0].kind != target["kind"]:
            raise ValueError("Regeneration did not preserve the requested section.")
    else:
        expected = Counter({kind:1 for kind in ["objectives","introduction","readings","notes","announcement","assignment","rubric"]})
        expected["quiz"] = questions
        if Counter(s.kind for s in generated.sections) != expected:
            raise ValueError("Generated section counts do not match the approved course options.")
    for section in generated.sections:
        if section.kind == "quiz" and (not section.answer or not section.explanation):
            raise ValueError("A quiz response is missing its answer or explanation.")
        if section.kind != "quiz" and (section.answer is not None or section.explanation is not None):
            raise ValueError("Answer-key fields are only permitted on quiz sections.")


def ground_sections(generated: GeneratedCourse, passages: list[dict], verification: Verification | None) -> list[dict]:
    sources = {p["id"]:p for p in passages}
    results = {}
    duplicates = set()
    for result in verification.results if verification else []:
        if result.section_id in results:
            duplicates.add(result.section_id)
        results[result.section_id] = result
    grounded = []
    for order, model in enumerate(generated.sections):
        section = model.model_dump()
        notes = []
        if model.kind not in PROPOSALS and not model.evidence:
            notes.append("Missing evidence for factual content or assessment premises.")
        for evidence in model.evidence:
            source = sources.get(evidence.passage_id)
            if source is None:
                notes.append("An evidence reference does not resolve to a selected source passage.")
            elif evidence.quote not in source["text"]:
                notes.append("An evidence quote is not an exact match to its source passage.")
        result = results.get(model.id)
        if not result or model.id in duplicates:
            notes.append("Independent support validation is missing or ambiguous for this section.")
        elif result.status != "supported":
            notes.append(f"Evidence review: {result.status}. {result.reason}")
        if "Insufficient information in the supplied material" in " ".join([model.body, model.answer or "", model.explanation or ""]):
            notes.append("The supplied material does not contain sufficient information.")
        section.update(support_status="needs_review" if notes else ("proposal" if model.kind in PROPOSALS else "supported"),
                       review_notes=notes, edited=False, order=order)
        grounded.append(section)
    return grounded
