"""Optional, explicitly selected local OCR. Neither page images nor text leave this host."""
import importlib.util
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MAX_OCR_PAGES = 5
OCR_VERSION = "tesseract-eng-pgm-v1"
MAX_PIXELS = 16_000_000
MAX_OCR_TEXT = 250_000
PAGE_TIMEOUT = 30


class OCRError(ValueError):
    pass


def validate_pages(pages, page_count=100):
    if pages is None:
        return []
    if not isinstance(pages, list) or len(pages) > MAX_OCR_PAGES:
        raise OCRError("Select at most 5 PDF pages for local OCR.")
    if any(type(p) is not int or p < 1 or p > min(page_count, 100) for p in pages):
        raise OCRError("OCR page numbers must be whole numbers within this PDF (1–100).")
    if len(set(pages)) != len(pages):
        raise OCRError("Select each OCR page only once.")
    return sorted(pages)


def _process_options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def ocr_capability():
    result = {"available": False, "reason": "", "max_pages": MAX_OCR_PAGES, "language": "eng"}
    if importlib.util.find_spec("pypdfium2") is None:
        result["reason"] = "Install the optional backend/requirements-ocr.txt packages, then restart Easy Street."
        return result
    executable = shutil.which("tesseract")
    if not executable:
        result["reason"] = "Install Tesseract with English language data and add it to PATH, then restart Easy Street."
        return result
    try:
        status = subprocess.run([executable, "--list-langs"], capture_output=True, timeout=5, check=False,
                                **_process_options())
        languages = status.stdout.decode("utf-8", errors="replace").splitlines()
        if status.returncode or "eng" not in [line.strip() for line in languages]:
            result["reason"] = "Tesseract English language data (eng) is unavailable. Install it and restart Easy Street."
            return result
    except (OSError, subprocess.TimeoutExpired):
        result["reason"] = "Tesseract could not be started. Check its installation and restart Easy Street."
        return result
    result.update(available=True, reason="Local English OCR is ready. Select up to 5 pages per upload.")
    return result


def ocr_pdf(data: bytes, pages: list[int]) -> dict[int, str]:
    pages = validate_pages(pages)
    if not pages:
        return {}
    capability = ocr_capability()
    if not capability["available"]:
        raise OCRError(capability["reason"])
    # Rendering runs in a separate process: PDFium is not safe for concurrent threads.
    # The subprocess also bounds a malformed document's rendering time.
    with tempfile.TemporaryDirectory(prefix="easy-street-ocr-") as folder:
        source = Path(folder) / "source.pdf"
        source.write_bytes(data)
        result = {}
        try:
            for page in pages:
                image = Path(folder) / f"page-{page}.pgm"
                text_base = Path(folder) / f"page-{page}"
                command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(source), str(image), str(page)]
                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=PAGE_TIMEOUT, check=True, **_process_options())
                subprocess.run([shutil.which("tesseract"), str(image), str(text_base), "-l", "eng", "--psm", "3"],
                               timeout=PAGE_TIMEOUT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               **_process_options())
                with text_base.with_suffix(".txt").open("r", encoding="utf-8") as stream:
                    text = stream.read(MAX_OCR_TEXT + 1)
                if len(text) > MAX_OCR_TEXT:
                    raise OCRError("Local OCR returned too much text. Try a smaller chapter.")
                result[page] = text
            return result
        except subprocess.TimeoutExpired as exc:
            raise OCRError("Local OCR timed out. Try fewer pages or a smaller, clearer PDF.") from exc
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            if isinstance(exc, OCRError):
                raise
            raise OCRError("Local OCR could not read these pages. Check the local installation and try again.") from exc


def _render_page(page, target):
    width, height = page.get_size()
    if not all(math.isfinite(v) and v > 0 for v in (width, height)):
        raise OCRError("Invalid PDF page dimensions.")
    scale = min(200 / 72, math.sqrt(MAX_PIXELS / (width * height)), 8000 / max(width, height))
    bitmap = page.render(scale=scale, grayscale=True, may_draw_forms=False, draw_annots=False,
                         limit_image_cache=True)
    try:
        if bitmap.width * bitmap.height > MAX_PIXELS + 16000 or bitmap.n_channels != 1:
            raise OCRError("PDF page exceeds the OCR image limit.")
        pixels = bytes(bitmap.buffer)
        with target.open("wb") as stream:
            stream.write(f"P5\n{bitmap.width} {bitmap.height}\n255\n".encode("ascii"))
            for row in range(bitmap.height):
                stream.write(pixels[row * bitmap.stride:row * bitmap.stride + bitmap.width])
    finally:
        bitmap.close()


def _worker(source, output, number):
    import pypdfium2
    with pypdfium2.PdfDocument(source) as pdf:
        validate_pages([number], len(pdf))
        page = pdf[number - 1]
        try:
            _render_page(page, Path(output))
        finally:
            page.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 5 or sys.argv[1] != "--worker":
            raise OCRError("Invalid OCR invocation.")
        _worker(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    except Exception:
        # Do not leak document text, local file paths, or subprocess output in logs.
        sys.exit(1)
