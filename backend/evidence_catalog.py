"""Deterministic, complete source excerpts for provider-selected evidence IDs."""
import copy
import re
from enum import Enum
from pydantic import Field, create_model
from .models import GeneratedCourse, GeneratedSection, StrictModel

MAX_CATALOG_ENTRIES = 512
MAX_CATALOG_SOURCE_CHARS = 24_000
MAX_QUOTE_CHARS = 500


def build_catalog(passages: list[dict]) -> list[dict]:
    if not passages or sum(len(p["text"]) for p in passages) > MAX_CATALOG_SOURCE_CHARS:
        raise ValueError("The selected source does not fit the bounded evidence catalog. Select a smaller chapter.")
    if len({p["id"] for p in passages}) != len(passages):
        raise ValueError("The selected source contains duplicate passage identifiers.")
    catalog = []
    for passage in passages:
        text = passage["text"]
        if not text:
            raise ValueError("An empty source passage cannot be represented in the evidence catalog.")
        start = 0
        while start < len(text):
            window = text[start:start + MAX_QUOTE_CHARS]
            # Prefer a complete sentence after at least 80 characters, keeping catalog
            # size bounded even for sources containing many very short sentences.
            boundary = next((m.end() for m in re.finditer(r"(?<=[.!?])\s+", window) if m.end() >= 80), None)
            if boundary is None:
                boundary = len(window)
                if start + boundary < len(text):
                    whitespace = [m.end() for m in re.finditer(r"\s+", window) if m.end() >= 80]
                    if whitespace:
                        boundary = whitespace[-1]
            quote = text[start:start + boundary]
            catalog.append({"id":f"e{len(catalog)+1:04d}", "passage_id":passage["id"],
                            "location":passage.get("location",passage["id"]), "quote":quote})
            start += boundary
            if len(catalog) > MAX_CATALOG_ENTRIES:
                raise ValueError("The selected source needs too many evidence excerpts. Select a smaller chapter; no source passages were silently dropped.")
    return catalog


def prepare_generation(payload: dict):
    catalog = build_catalog(payload["passages"])
    # One enum is reused by every section. The catalog plus the section-kind enum
    # stays below the provider's total enum limit; short IDs bound enum string size.
    evidence_ids = Enum("EvidenceId", {entry["id"]:entry["id"] for entry in catalog}, type=str)
    # Module/assessment membership comes from the approved plan, not provider output.
    fields = {name:(field.annotation,copy.deepcopy(field)) for name,field in GeneratedSection.model_fields.items() if name not in ("evidence","module_id","assessment_id")}
    fields["evidence_ids"] = (list[evidence_ids],Field(max_length=12))
    target = payload.get("target_section")
    if target:
        # Constrain regeneration structurally rather than trusting a prose instruction.
        # Reject extra sections or changed identity instead of silently filtering them.
        fields["id"] = (Enum("TargetSectionId",{"target":target["id"]},type=str),Field())
        fields["kind"] = (Enum("TargetSectionKind",{"target":target["kind"]},type=str),Field())
    section_schema = create_model("EvidenceReferencedSection",__base__=StrictModel,**fields)
    schema = create_model("EvidenceReferencedCourse",__base__=StrictModel,
                          sections=(list[section_schema],Field(min_length=1,max_length=1 if target else 20)))
    prepared = {k:v for k,v in payload.items() if k != "passages"}
    prepared["generation_mode"] = "regenerate_section" if target else "full_course"
    prepared["evidence_catalog"] = catalog
    return prepared,schema,catalog


def expand_evidence(parsed, schema, catalog) -> GeneratedCourse:
    # Validate again at the boundary even when a substituted client bypasses SDK parsing.
    value = parsed.model_dump(mode="json") if hasattr(parsed,"model_dump") else parsed
    validated = schema.model_validate(value).model_dump(mode="json")
    lookup = {entry["id"]:entry for entry in catalog}
    for section in validated["sections"]:
        selected = section.pop("evidence_ids")
        section["evidence"] = []
        for identifier in dict.fromkeys(selected):
            if identifier not in lookup:
                raise ValueError("The provider selected an unknown evidence identifier.")
            entry = lookup[identifier]
            section["evidence"].append({"passage_id":entry["passage_id"],"quote":entry["quote"]})
    return GeneratedCourse.model_validate(validated)
