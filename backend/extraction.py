"""Local extraction. Source strings are data and are never executable instructions."""
import hashlib
import io
import re
from pathlib import Path
from pypdf import PdfReader

MAX_UPLOAD = 15 * 1024 * 1024
MAX_PAGES = 100
MAX_CHARS = 250_000
SAMPLE_PATH = Path(__file__).parent / "sample" / "chapter.txt"


class ExtractionError(ValueError):
    pass


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\x00", "")).strip()


def extract(data: bytes, filename: str) -> dict:
    if len(data) > MAX_UPLOAD:
        raise ExtractionError("File exceeds the 15 MiB upload limit.")
    digest = hashlib.sha256(data).hexdigest()
    doc_id = digest[:24]
    ext = Path(filename).suffix.lower()
    passages, warnings = [], []
    if ext == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ExtractionError("This file does not contain a valid PDF header.")
        try:
            reader = PdfReader(io.BytesIO(data), strict=False)
            if reader.is_encrypted:
                raise ExtractionError("Encrypted PDFs are not supported. Upload a readable, unencrypted copy.")
            if len(reader.pages) > MAX_PAGES:
                raise ExtractionError("The first milestone accepts chapters of up to 100 pages.")
            total = 0
            for index, page in enumerate(reader.pages, 1):
                value = clean(page.extract_text() or "")
                total += len(value)
                if total > MAX_CHARS:
                    raise ExtractionError("This chapter contains too much text. Split it into smaller chapters.")
                if len(value) < 40:
                    warnings.append(f"Page {index} has little or no readable text; it may need local OCR.")
                blocks = [clean(b) for b in re.split(r"\n\s*\n", value) if clean(b)]
                # Large single blocks are split without losing the real page reference.
                blocks = [chunk for b in blocks for chunk in split_block(b)]
                for paragraph, block in enumerate(blocks, 1):
                    passages.append({"id":f"{doc_id}-p{index:04d}-b{paragraph:04d}", "document_id":doc_id, "text":block,
                        "location":f"Page {index}, passage {paragraph}", "page":index, "paragraph":paragraph, "heading":block.splitlines()[0][:120]})
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError("The PDF could not be read. Try an unencrypted, readable chapter PDF.") from exc
        warnings.append("PDF extraction does not reliably preserve images, tables, or equations. Review the preview; no OCR or paid vision service was used.")
    elif ext == ".txt":
        try:
            value = clean(data.decode("utf-8-sig"))
        except UnicodeDecodeError as exc:
            raise ExtractionError("Text files must use UTF-8 encoding.") from exc
        if len(value) > MAX_CHARS:
            raise ExtractionError("This chapter contains too much text. Split it into smaller chapters.")
        blocks = [clean(b) for b in re.split(r"\n\s*\n", value) if clean(b)]
        for index, block in enumerate([c for b in blocks for c in split_block(b)], 1):
            passages.append({"id":f"{doc_id}-t{index:04d}", "document_id":doc_id,"text":block,
                "location":f"Paragraph {index}","page":None,"paragraph":index,"heading":block.splitlines()[0][:120]})
    else:
        raise ExtractionError("Upload a readable PDF or UTF-8 TXT file. DOCX and OCR are planned for later.")
    if sum(len(p["text"]) for p in passages) < 150:
        raise ExtractionError("Too little readable text was extracted. Supply a text-based chapter or a local OCR copy.")
    if len(passages) < 3:
        warnings.append("This source has limited separable coverage; review the proposed assessments for repetition.")
    return {"id":doc_id,"filename":Path(filename).name[:180],"sha256":digest,"format":ext[1:],"passages":passages,
            "warnings":warnings,"is_sample":digest == hashlib.sha256(SAMPLE_PATH.read_bytes()).hexdigest()}


def split_block(block: str) -> list[str]:
    # Deterministic boundaries preserve exact quotations, even with irregular PDF line breaks.
    return [block[i:i+3500] for i in range(0, len(block), 3500)]


def select_passages(document: dict) -> list[dict]:
    selected, length = [], 0
    for passage in document["passages"]:
        if length + len(passage["text"]) > 24_000:
            break
        selected.append(passage)
        length += len(passage["text"])
    return selected
