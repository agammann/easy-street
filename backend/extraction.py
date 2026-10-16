"""Local extraction. Source strings are data and are never executable instructions."""
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile
from pypdf import PdfReader
from .ocr import OCR_VERSION, OCRError, ocr_pdf, validate_pages

MAX_UPLOAD = 15 * 1024 * 1024
MAX_PAGES = 100
MAX_CHARS = 250_000
MAX_DOCX_ENTRIES = 512
MAX_DOCX_EXPANDED = 32 * 1024 * 1024
MAX_DOCX_XML = 4 * 1024 * 1024
SAMPLE_PATH = Path(__file__).parent / "sample" / "chapter.txt"


class ExtractionError(ValueError):
    pass


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\x00", "")).strip()


def extract(data: bytes, filename: str, ocr_pages=None, allow_ocr_preview=False) -> dict:
    if len(data) > MAX_UPLOAD:
        raise ExtractionError("File exceeds the 15 MiB upload limit.")
    digest = hashlib.sha256(data).hexdigest()
    doc_id = digest[:24]
    ext = Path(filename).suffix.lower()
    try:
        selected_ocr_pages = validate_pages(ocr_pages)
    except OCRError as exc:
        raise ExtractionError(str(exc)) from exc
    if selected_ocr_pages and ext != ".pdf":
        raise ExtractionError("Local OCR page selection is available only for PDF files.")
    passages, warnings, needs_ocr_pages = [], [], []
    page_count = None
    if ext == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ExtractionError("This file does not contain a valid PDF header.")
        try:
            reader = PdfReader(io.BytesIO(data), strict=False)
            if reader.is_encrypted:
                raise ExtractionError("Encrypted PDFs are not supported. Upload a readable, unencrypted copy.")
            page_count = len(reader.pages)
            if page_count > MAX_PAGES:
                raise ExtractionError("Upload a chapter of up to 100 pages.")
            selected_ocr_pages = validate_pages(selected_ocr_pages, page_count)
            ocr_text = ocr_pdf(data, selected_ocr_pages) if selected_ocr_pages else {}
            if selected_ocr_pages:
                identity = json.dumps([digest, OCR_VERSION, selected_ocr_pages, ocr_text], sort_keys=True)
                doc_id = hashlib.sha256(identity.encode()).hexdigest()[:24]
            total = 0
            for index, page in enumerate(reader.pages, 1):
                recognized = clean(ocr_text.get(index, ""))
                value = recognized or clean(page.extract_text() or "")
                if index in ocr_text:
                    if not recognized:
                        warnings.append(f"Local OCR found no text on page {index}; any existing text was retained.")
                total += len(value)
                if total > MAX_CHARS:
                    raise ExtractionError("This chapter contains too much text. Split it into smaller chapters.")
                if len(value) < 40:
                    warnings.append(f"Page {index} has little or no readable text; it may need local OCR.")
                    needs_ocr_pages.append(index)
                blocks = [clean(b) for b in re.split(r"\n\s*\n", value) if clean(b)]
                # Large single blocks are split without losing the real page reference.
                blocks = [chunk for b in blocks for chunk in split_block(b)]
                for paragraph, block in enumerate(blocks, 1):
                    passages.append({"id":f"{doc_id}-p{index:04d}-b{paragraph:04d}", "document_id":doc_id, "text":block,
                        "location":f"Page {index}, passage {paragraph}", "page":index, "paragraph":paragraph,
                        "heading":block.splitlines()[0][:120], "ocr":index in ocr_text and bool(clean(ocr_text[index]))})
        except OCRError as exc:
            raise ExtractionError(str(exc)) from exc
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError("The PDF could not be read. Try an unencrypted, readable chapter PDF.") from exc
        warnings.append("PDF extraction does not reliably preserve images, tables, or equations. Review the preview; no paid vision service was used.")
        if selected_ocr_pages:
            warnings.append("Local English OCR was used on pages " + ", ".join(map(str, selected_ocr_pages)) +
                            ". Recognition can be wrong; compare these passages with the original pages before generating a course.")
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
    elif ext == ".docx":
        passages, docx_warnings = extract_docx(data, doc_id)
        warnings.extend(docx_warnings)
    else:
        raise ExtractionError("Upload a PDF, DOCX, or UTF-8 TXT file.")
    insufficient_text = sum(len(p["text"]) for p in passages) < 150
    if insufficient_text:
        if ext != ".pdf" or not allow_ocr_preview:
            raise ExtractionError("Too little readable text was extracted. Supply a text-based chapter or a local OCR copy.")
        warnings.append("Too little readable text is available to create a course. Select pages for local OCR or upload a readable copy.")
    if len(passages) < 3:
        warnings.append("This source has limited separable coverage; review the proposed assessments for repetition.")
    return {"id":doc_id,"filename":Path(filename).name[:180],"sha256":digest,"format":ext[1:],"passages":passages,
            "warnings":warnings,"is_sample":digest == hashlib.sha256(SAMPLE_PATH.read_bytes()).hexdigest(),
            "page_count":page_count, "ocr_pages":selected_ocr_pages, "needs_ocr_pages":needs_ocr_pages,
            "insufficient_text":insufficient_text}


def _xml_part(archive, name):
    info = archive.getinfo(name)
    if info.file_size > MAX_DOCX_XML:
        raise ExtractionError("A DOCX XML part is too large. Split the source into smaller chapters.")
    with archive.open(info) as stream:
        data = stream.read(MAX_DOCX_XML + 1)
    if len(data) > MAX_DOCX_XML:
        raise ExtractionError("A DOCX XML part is too large. Split the source into smaller chapters.")
    # XML may be UTF-16. Decode before checking declarations so null bytes cannot hide them.
    probe = data.decode("utf-16") if data.startswith((b"\xff\xfe", b"\xfe\xff")) else data.decode("utf-8-sig")
    if "\x00" in probe or re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", probe, flags=re.IGNORECASE):
        raise ExtractionError("DOCX XML entity declarations are not supported.")
    return ET.fromstring(probe)


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _paragraph_text(element):
    parts = []
    pending = [element]
    while pending:
        node = pending.pop()
        name = _local_name(node.tag)
        if name in {"del", "moveFrom", "txbxContent", "oMath", "oMathPara"}:
            continue
        if name == "t":
            parts.append(node.text or "")
        elif name in {"tab", "br", "cr"}:
            parts.append("\n" if name != "tab" else "\t")
        pending.extend(reversed(list(node)))
    return clean("".join(parts))


def _body_paragraphs(body):
    pending = [body]
    while pending:
        node = pending.pop()
        name = _local_name(node.tag)
        if name in {"del", "moveFrom", "txbxContent"}:
            continue
        if name == "p":
            yield node
        else:
            pending.extend(reversed(list(node)))


def extract_docx(data, doc_id):
    warnings = ["DOCX uses paragraph locations, not page numbers. Images, equations, headers, footers, comments, and footnotes are not extracted; review the preview."]
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_DOCX_ENTRIES or sum(item.file_size for item in entries) > MAX_DOCX_EXPANDED:
                raise ExtractionError("The DOCX archive is too large or complex. Split it into smaller chapters.")
            names = [item.filename for item in entries]
            if len(set(names)) != len(names):
                raise ExtractionError("The DOCX contains duplicate archive entries.")
            for item in entries:
                path = PurePosixPath(item.filename)
                if item.flag_bits & 1 or path.is_absolute() or ".." in path.parts or "\\" in item.filename:
                    raise ExtractionError("Encrypted or malformed DOCX archives are not supported.")
                lowered = item.filename.lower()
                if "vbaproject" in lowered or lowered.startswith(("word/embeddings/", "word/activex/")):
                    raise ExtractionError("DOCX files with macros or embedded objects are not supported. Save a plain DOCX copy.")
            types = _xml_part(archive, "[Content_Types].xml")
            if any("macroenabled" in item.attrib.get("ContentType", "").lower() for item in types):
                raise ExtractionError("Macro-enabled Word documents are not supported. Save a plain DOCX copy.")
            document = _xml_part(archive, "word/document.xml")
            namespace = document.tag.partition("}")[0].lstrip("{")
            if namespace not in {"http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                                 "http://purl.oclc.org/ooxml/wordprocessingml/main"}:
                raise ExtractionError("This file does not contain a readable DOCX document.")
            prefix = "{" + namespace + "}"
            body = document.find(prefix + "body")
            if body is None:
                raise ExtractionError("This DOCX has no document body.")
            heading_styles = set()
            if "word/styles.xml" in names:
                styles = _xml_part(archive, "word/styles.xml")
                for style in styles:
                    label = style.find(prefix + "name")
                    label = label.get(prefix + "val", "") if label is not None else ""
                    if re.fullmatch(r"heading\s*[1-9]", label, re.IGNORECASE) or style.find(".//" + prefix + "outlineLvl") is not None:
                        heading_styles.add(style.get(prefix + "styleId", ""))
            passages, heading, total = [], "", 0
            # Iterating body paragraphs preserves document order, including table cells.
            for index, paragraph in enumerate(_body_paragraphs(body), 1):
                text = _paragraph_text(paragraph)
                if not text:
                    continue
                total += len(text)
                if total > MAX_CHARS:
                    raise ExtractionError("This chapter contains too much text. Split it into smaller chapters.")
                style = paragraph.find("./" + prefix + "pPr/" + prefix + "pStyle")
                style_id = style.get(prefix + "val", "") if style is not None else ""
                if style_id in heading_styles or re.fullmatch(r"Heading[1-9]", style_id, re.IGNORECASE):
                    heading = text[:120]
                for chunk, block in enumerate(split_block(text), 1):
                    passages.append({"id":f"{doc_id}-d{index:04d}-b{chunk:04d}", "document_id":doc_id,
                                     "text":block, "location":f"Paragraph {index}" + (f", passage {chunk}" if chunk > 1 else ""),
                                     "page":None, "paragraph":index, "heading":heading or block.splitlines()[0][:120]})
            if any(True for _ in body.iter(prefix + "tbl")):
                warnings.append("DOCX table cells were read in document order; row and column meaning may be lost. Review table passages carefully.")
            if any(_local_name(node.tag) in {"del", "moveFrom", "ins", "moveTo"} for node in body.iter()):
                warnings.append("Tracked changes were read as the current text: inserted text is included and deleted text is omitted.")
            return passages, warnings
    except ExtractionError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeError, OSError, RuntimeError, ValueError) as exc:
        raise ExtractionError("The DOCX could not be read. Try an unencrypted, plain DOCX chapter.") from exc


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
