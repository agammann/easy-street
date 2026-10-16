import io
from pathlib import Path
import subprocess
from types import SimpleNamespace
import zipfile

import pytest
from pypdf import PdfWriter

from backend import extraction, ocr
from backend.extraction import ExtractionError, SAMPLE_PATH, extract


NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SOURCE = "Observe the soil below the surface before deciding whether to water. Water slowly when the soil feels dry, and record the observation and action for each container."


def docx_bytes(body=None, extra=None, document=None):
    if body is None:
        body = f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Observing soil</w:t></w:r></w:p><w:p><w:r><w:t>{SOURCE}</w:t></w:r></w:p>'
    parts = {
        "[Content_Types].xml": '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>',
        "_rels/.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/_rels/document.xml.rels": '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
        "word/document.xml": document or f'<w:document xmlns:w="{NS}"><w:body>{body}</w:body></w:document>',
        "word/styles.xml": f'<w:styles xmlns:w="{NS}"><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style></w:styles>',
    }
    parts.update(extra or {})
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in parts.items():
            archive.writestr(name, value)
    return stream.getvalue()


def blank_pdf(pages=2):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def test_docx_preserves_heading_paragraph_and_stable_identity():
    data = docx_bytes()
    a = extract(data, "chapter.docx")
    b = extract(data, "renamed.docx")
    assert a["id"] == b["id"]
    assert a["passages"][1]["text"] == SOURCE
    assert a["passages"][1]["heading"] == "Observing soil"
    assert a["passages"][1]["location"] == "Paragraph 2"
    assert all(item["page"] is None for item in a["passages"])
    assert not a["insufficient_text"] and a["ocr_pages"] == []


def test_docx_tables_and_tracked_changes_have_explicit_limits():
    body = f'<w:tbl><w:tr><w:tc><w:p><w:r><w:t>{SOURCE}</w:t></w:r><w:del><w:r><w:t>DELETED</w:t></w:r></w:del><w:ins><w:r><w:t> Current revision.</w:t></w:r></w:ins></w:p></w:tc></w:tr></w:tbl>'
    doc = extract(docx_bytes(body), "table.docx")
    assert doc["passages"][0]["text"] == SOURCE + " Current revision."
    assert any("table cells" in warning for warning in doc["warnings"])
    assert any("Tracked changes" in warning for warning in doc["warnings"])


@pytest.mark.parametrize("extra", [{"../outside.xml":"bad"}, {"word/vbaProject.bin":"bad"},
                                  {"word/embeddings/oleObject1.bin":"bad"}])
def test_docx_rejects_unsafe_packages(extra):
    with pytest.raises(ExtractionError):
        extract(docx_bytes(extra=extra), "unsafe.docx")


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_docx_rejects_xml_entities_before_parsing(encoding):
    xml = f'<!DOCTYPE document [<!ENTITY injected "{SOURCE}">]><w:document xmlns:w="{NS}"><w:body><w:p><w:r><w:t>&injected;</w:t></w:r></w:p></w:body></w:document>'
    with pytest.raises(ExtractionError, match="entity declarations"):
        extract(docx_bytes(document=xml.encode(encoding)), "entity.docx")


def test_docx_expansion_and_text_limits(monkeypatch):
    monkeypatch.setattr(extraction, "MAX_DOCX_EXPANDED", 20)
    with pytest.raises(ExtractionError, match="too large"):
        extract(docx_bytes(), "large.docx")
    monkeypatch.setattr(extraction, "MAX_DOCX_EXPANDED", 32 * 1024 * 1024)
    monkeypatch.setattr(extraction, "MAX_CHARS", 50)
    with pytest.raises(ExtractionError, match="too much text"):
        extract(docx_bytes(), "large.docx")


def test_scanned_preview_requires_explicit_ocr_and_preserves_original(monkeypatch):
    data = blank_pdf()
    calls = []
    def recognize(source, pages):
        calls.append(pages)
        return {page: SOURCE for page in pages}
    monkeypatch.setattr(extraction, "ocr_pdf", recognize)
    preview = extract(data, "scan.pdf", allow_ocr_preview=True)
    assert calls == []
    assert preview["passages"] == [] and preview["insufficient_text"]
    assert preview["needs_ocr_pages"] == [1, 2]
    result = extract(data, "scan.pdf", ocr_pages=[2], allow_ocr_preview=True)
    assert calls == [[2]]
    assert result["sha256"] == preview["sha256"] and result["id"] != preview["id"]
    assert result["ocr_pages"] == [2] and result["needs_ocr_pages"] == [1]
    assert result["passages"][0]["page"] == 2 and result["passages"][0]["ocr"]
    assert not result["insufficient_text"]
    assert extract(data, "scan.pdf", ocr_pages=[2])["id"] == result["id"]


@pytest.mark.parametrize("pages", [[0], [3], [True], ["1"], [1, 1], list(range(1, 7))])
def test_invalid_ocr_selection_is_rejected_before_ocr(monkeypatch, pages):
    monkeypatch.setattr(extraction, "ocr_pdf", lambda *_: pytest.fail("OCR must not run"))
    with pytest.raises(ExtractionError):
        extract(blank_pdf(), "scan.pdf", ocr_pages=pages, allow_ocr_preview=True)


def test_optional_ocr_missing_dependency_and_timeout_are_actionable(monkeypatch):
    monkeypatch.setattr(ocr.importlib.util, "find_spec", lambda _: None)
    assert not ocr.ocr_capability()["available"]
    with pytest.raises(ocr.OCRError, match="requirements-ocr"):
        ocr.ocr_pdf(blank_pdf(), [1])
    monkeypatch.setattr(ocr, "ocr_capability", lambda: {"available":True})
    def timeout(command, **kwargs):
        assert kwargs["timeout"] == ocr.PAGE_TIMEOUT
        assert kwargs["stdout"] == subprocess.DEVNULL
        raise subprocess.TimeoutExpired(command, 30)
    monkeypatch.setattr(ocr.subprocess, "run", timeout)
    with pytest.raises(ocr.OCRError, match="timed out"):
        ocr.ocr_pdf(blank_pdf(), [1])


def test_ocr_processes_use_explicit_arguments_and_clean_temporary_files(monkeypatch):
    monkeypatch.setattr(ocr, "ocr_capability", lambda: {"available":True})
    monkeypatch.setattr(ocr.shutil, "which", lambda _: "tesseract")
    calls, folders = [], []
    def run(command, **kwargs):
        calls.append(command)
        assert isinstance(command, list) and not kwargs.get("shell")
        if command[0] == "tesseract":
            Path(command[2]).with_suffix(".txt").write_text(SOURCE, encoding="utf-8")
            folders.append(Path(command[2]).parent)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(ocr.subprocess, "run", run)
    assert ocr.ocr_pdf(blank_pdf(), [2]) == {2:SOURCE}
    assert len(calls) == 2 and calls[0][-1] == "2"
    assert calls[1][-4:] == ["-l", "eng", "--psm", "3"]
    assert not folders[0].exists()


def test_sample_docx_matches_original_source():
    path = SAMPLE_PATH.with_suffix(".docx")
    doc = extract(path.read_bytes(), path.name)
    original = SAMPLE_PATH.read_text(encoding="utf-8")
    assert all(item["text"] in original for item in doc["passages"])
    assert len(doc["passages"]) >= 6


def test_real_local_ocr_recognizes_original_sample():
    if not ocr.ocr_capability()["available"]:
        pytest.skip("Optional local Tesseract and pypdfium2 are not installed")
    # Rendering the original PDF to pixels and recognizing it exercises both real binaries.
    doc = extract(SAMPLE_PATH.with_suffix(".pdf").read_bytes(), "chapter.pdf", ocr_pages=[1])
    recognized = " ".join(p["text"] for p in doc["passages"] if p["page"] == 1).lower()
    assert "soil" in recognized and "water" in recognized
    assert len(recognized) > 150 and doc["ocr_pages"] == [1]
    assert all(p["ocr"] for p in doc["passages"] if p["page"] == 1)
