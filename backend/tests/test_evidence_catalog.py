import json
from collections import defaultdict
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from backend.evidence_catalog import build_catalog, prepare_generation, expand_evidence, MAX_CATALOG_ENTRIES
from backend.extraction import extract, SAMPLE_PATH
from backend.main import create_app
from backend.provider import (GENERATION_INSTRUCTIONS, generation_input_bound, input_token_bound,
                              verification_input_bound, estimate, MAX_GENERATION_TOKENS)


def reference_output(ids):
    return {"sections":[{"id":"notes", "kind":"notes", "title":"Notes", "body":"Read the source.",
                         "answer":None,"explanation":None,"evidence_ids":ids}]}


def test_catalog_covers_every_original_character_in_order_with_contiguous_quotes():
    document = extract(SAMPLE_PATH.with_suffix(".pdf").read_bytes(),"sample.pdf")
    passages = document["passages"] + [{"id":"short-heading","text":"A","location":"Paragraph 2"},
        {"id":"long-sentence","text":"Unicode café soil observation " * 90,"location":"Paragraph 3"}]
    catalog = build_catalog(passages)
    grouped = defaultdict(list)
    lookup = {p["id"]:p["text"] for p in passages}
    for entry in catalog:
        assert 1 <= len(entry["quote"]) <= 500
        assert entry["quote"] in lookup[entry["passage_id"]]
        grouped[entry["passage_id"]].append(entry["quote"])
    assert {id:"".join(quotes) for id,quotes in grouped.items()} == lookup
    assert len({e["id"] for e in catalog}) == len(catalog)
    assert catalog == build_catalog(passages)


def test_catalog_enum_resolves_selected_ids_only_to_original_quotes():
    payload = {"passages":[{"id":"p1","text":"One source fact. " * 20,"location":"Page 1"}]}
    prepared,schema,catalog = prepare_generation(payload)
    chosen = [catalog[0]["id"],catalog[-1]["id"],catalog[0]["id"]]
    result = expand_evidence(reference_output(chosen),schema,catalog)
    assert [e.model_dump() for e in result.sections[0].evidence] == [
        {"passage_id":e["passage_id"],"quote":e["quote"]} for e in (catalog[0],catalog[-1])]
    assert "passages" not in prepared
    assert schema.model_json_schema()["$defs"]["EvidenceId"]["enum"] == [e["id"] for e in catalog]
    with pytest.raises(ValidationError):
        expand_evidence(reference_output(["e9999"]),schema,catalog)
    altered = reference_output([catalog[0]["id"]])
    altered["sections"][0]["quote"] = "Invented or stitched quote..."
    with pytest.raises(ValidationError):
        expand_evidence(altered,schema,catalog)


def test_budget_counts_actual_catalog_schema_and_verifier_quote_expansion():
    payload = {"passages":[{"id":"p1","text":"Bounded source observation. " * 150,"location":"Page 1"}]}
    prepared,schema,catalog = prepare_generation(payload)
    generation_bound = generation_input_bound(payload)
    actual_bytes = (len(json.dumps(prepared,ensure_ascii=False).encode())
                    + len(json.dumps(schema.model_json_schema(),ensure_ascii=False).encode())
                    + len(GENERATION_INSTRUCTIONS.encode()))
    assert generation_bound == actual_bytes + 8192
    expected_expansion = 20 * sum(sorted((len(json.dumps({"passage_id":e["passage_id"],"quote":e["quote"]},ensure_ascii=False).encode()) + 2 for e in catalog),reverse=True)[:12])
    verification_bound = verification_input_bound({"passages":payload["passages"],"sections":[]})
    assert estimate(payload)["input_tokens_estimate"] == generation_bound + verification_bound + MAX_GENERATION_TOKENS * 32 + expected_expansion


def test_catalog_overflow_is_rejected_before_any_job_or_provider_call(tmp_path):
    class NeverCalled:
        def generate(self,payload):
            pytest.fail("Catalog rejection must happen before a paid generation request.")
        def verify(self,payload):
            pytest.fail("Catalog rejection must happen before a paid verification request.")
    app = create_app(tmp_path,provider=NeverCalled(),budget_limit=10)
    client = TestClient(app,base_url="http://localhost")
    source = "\n\n".join(["A"] * (MAX_CATALOG_ENTRIES + 1))
    doc = client.post("/api/documents",files={"file":("too-many-passages.txt",source.encode(),"text/plain")}).json()
    course = client.post("/api/courses",json={"document_id":doc["id"],"title":"Bounded catalog","mode":"openai"}).json()
    assert client.post(f"/api/courses/{course['id']}/approve",json={"provider_disclosure_accepted":True}).status_code == 200
    estimated = client.get(f"/api/courses/{course['id']}/estimate")
    submitted = client.post(f"/api/courses/{course['id']}/generate",json={"idempotency_key":"catalog-overflow-test"})
    assert estimated.status_code == submitted.status_code == 400
    assert "smaller chapter" in estimated.json()["detail"]
    assert app.state.service.store.all("jobs") == []
    assert app.state.service.store.budget()["reserved_usd"] == 0


def test_source_character_bound_never_truncates_catalog_silently():
    with pytest.raises(ValueError,match="smaller chapter"):
        build_catalog([{"id":"p1","text":"x" * 24_001}])


def test_regeneration_schema_requires_exactly_one_section_with_unchanged_identity():
    payload = {"passages":[{"id":"p1","text":"Observe the soil before watering."}],
               "target_section":{"id":"existing-notes","kind":"notes"}}
    prepared,schema,catalog = prepare_generation(payload)
    output = reference_output([catalog[0]["id"]])
    output["sections"][0]["id"] = "existing-notes"
    assert prepared["generation_mode"] == "regenerate_section"
    result = expand_evidence(output,schema,catalog)
    assert len(result.sections) == 1
    assert result.sections[0].id == "existing-notes" and result.sections[0].kind == "notes"
    # Regression: the real provider returned an entire course for a notes-only request.
    with pytest.raises(ValidationError):
        expand_evidence({"sections":output["sections"] * 2},schema,catalog)
    for changed in ({"id":"replacement-notes"},{"kind":"introduction"}):
        invalid = {"sections":[{**output["sections"][0],**changed}]}
        with pytest.raises(ValidationError):
            expand_evidence(invalid,schema,catalog)


def test_regeneration_adapter_sends_constrained_schema_and_expands_only_target(monkeypatch):
    from types import SimpleNamespace
    import openai
    from backend.provider import OpenAIProvider
    captured = {}
    class StubClient:
        def __init__(self,**kwargs):
            self.responses = self
        def parse(self,**kwargs):
            captured.update(kwargs)
            output = reference_output(["e0001"])
            output["sections"][0]["id"] = "saved-notes"
            return SimpleNamespace(output_parsed=kwargs["text_format"].model_validate(output),
                usage=SimpleNamespace(input_tokens=20,output_tokens=30),status="completed")
    monkeypatch.setattr(openai,"OpenAI",StubClient)
    result,_ = OpenAIProvider(api_key="test-placeholder").generate({
        "passages":[{"id":"p1","text":"Observe the soil before watering."}],
        "target_section":{"id":"saved-notes","kind":"notes"}})
    schema = captured["text_format"].model_json_schema()
    assert schema["properties"]["sections"]["minItems"] == schema["properties"]["sections"]["maxItems"] == 1
    assert schema["$defs"]["TargetSectionId"]["enum"] == ["saved-notes"]
    assert schema["$defs"]["TargetSectionKind"]["enum"] == ["notes"]
    assert json.loads(captured["input"])["generation_mode"] == "regenerate_section"
    assert len(result.sections) == 1 and result.sections[0].id == "saved-notes"
    assert result.sections[0].evidence[0].quote == "Observe the soil before watering."
