"""Recoverable course management and bounded, source-free backup import."""
import copy
import hashlib
import json
import re
import uuid
from collections import Counter
from fastapi import File, HTTPException, UploadFile
from pydantic import Field
from .models import CourseInput, GeneratedSection, StrictModel
from .store import now

MAX_BACKUP = 15 * 1024 * 1024
IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
IMPORT_NOTE = "Imported content needs review against the original source."


class ArchiveInput(StrictModel):
    archived: bool


class RestoreInput(StrictModel):
    version_id: int = Field(gt=0)


def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError("Backup contains an invalid identifier.")
    return value


def text(value, maximum=150):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError("Backup contains an invalid text field.")
    return value


def string_list(value, maximum=8, item_length=500):
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError("Backup contains an invalid list.")
    return [text(item, item_length) for item in value]


def parse_backup(data):
    if len(data) > MAX_BACKUP:
        raise ValueError("Course backups must be 15 MiB or smaller.")
    try:
        value = json.loads(data)
        if value.get("format") != "easy-street-course-v1" or value.get("source_text_included") is not False:
            raise ValueError("Choose an Easy Street course JSON export without source text.")
        source = value["source_manifest"]
        source_id = identifier(source["document_id"])
        digest = source["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Backup contains an invalid source hash.")
        filename = text(source["filename"], 180).replace("\\", "/").rsplit("/", 1)[-1]
        file_format = source.get("format", filename.rsplit(".", 1)[-1].lower())
        if file_format not in ("pdf", "txt", "docx"):
            raise ValueError("Backup contains an unsupported source type.")
        ocr_pages = source.get("ocr_pages", [])
        if not isinstance(ocr_pages, list) or len(ocr_pages) > 5 or any(type(p) is not int or not 1 <= p <= 100 for p in ocr_pages):
            raise ValueError("Backup contains invalid OCR page selections.")
        locations = source["passages"]
        if not isinstance(locations, list) or len(locations) > 250000:
            raise ValueError("Backup contains too many source references.")
        references = []
        for passage in locations:
            page, paragraph = passage.get("page"), passage["paragraph"]
            if page is not None and (type(page) is not int or not 1 <= page <= 100):
                raise ValueError("Backup contains an invalid page reference.")
            if type(paragraph) is not int or not 1 <= paragraph <= 1000000:
                raise ValueError("Backup contains an invalid paragraph reference.")
            references.append({"id":identifier(passage["id"]), "location":text(passage["location"], 250),
                               "page":page, "paragraph":paragraph})
        passage_ids = {p["id"] for p in references}
        if len(passage_ids) != len(references):
            raise ValueError("Backup contains duplicate source references.")
        raw = value["course"]
        options = CourseInput(document_id=source_id, title=raw["title"], difficulty=raw["difficulty"],
                              mode=raw["mode"], **raw["options"])
        original_outline = raw["outline"]
        outline = {"title":options.title, "module_title":text(original_outline["module_title"]),
                   "objectives":string_list(original_outline["objectives"]), "warnings":[IMPORT_NOTE]}
        selected = original_outline.get("selected_passage_ids", list(passage_ids))
        if not isinstance(selected, list) or len(selected) > 30000 or any(p not in passage_ids for p in selected):
            raise ValueError("Backup outline refers to an unknown source passage.")
        outline["selected_passage_ids"] = list(dict.fromkeys(selected))
        modules = original_outline.get("modules")
        if modules is not None:
            if not isinstance(modules, list) or len(modules) != options.modules:
                raise ValueError("Backup module count does not match its options.")
            outline["modules"] = []
            for module in modules:
                assignments, quizzes = module["assignments"], module["quizzes"]
                if any(type(n) is not int or not 0 <= n <= 2 for n in (assignments, quizzes)):
                    raise ValueError("Backup assessment distribution is invalid.")
                ids = module["selected_passage_ids"]
                if not isinstance(ids, list) or not ids or len(ids) > 5000 or any(p not in passage_ids for p in ids):
                    raise ValueError("Backup module refers to an unknown source passage.")
                outline["modules"].append({"id":identifier(module["id"]), "title":text(module["title"]),
                    "objectives":string_list(module["objectives"]), "selected_passage_ids":list(dict.fromkeys(ids)),
                    "assignments":assignments, "quizzes":quizzes})
            if len({m["id"] for m in outline["modules"]}) != len(modules):
                raise ValueError("Backup contains duplicate modules.")
            for key in ("assignments", "quizzes"):
                if sum(m[key] for m in outline["modules"]) != getattr(options, key):
                    raise ValueError("Backup assessment totals do not match its options.")
            outline["distribution"] = [{"module":i + 1,"assignments":m["assignments"],"quizzes":m["quizzes"],
                "questions":m["quizzes"] * options.questions_per_quiz} for i,m in enumerate(outline["modules"])]
            outline["course_objectives"] = list(dict.fromkeys(objective for m in outline["modules"] for objective in m["objectives"]))
        else:
            if options.modules != 1:
                raise ValueError("Multi-module backup is missing its module outline.")
            outline["distribution"] = [{"module":1,"assignments":options.assignments,"quizzes":options.quizzes,
                                        "questions":options.quizzes * options.questions_per_quiz}]
        raw_sections = raw["sections"]
        if not isinstance(raw_sections, list) or not 1 <= len(raw_sections) <= 120:
            raise ValueError("Backup must contain between one and 120 sections.")
        sections = []
        for order, section in enumerate(raw_sections):
            parsed = GeneratedSection.model_validate({k:v for k,v in section.items() if k in GeneratedSection.model_fields})
            if any(e.passage_id not in passage_ids for e in parsed.evidence):
                raise ValueError("Backup evidence refers to an unknown source passage.")
            if parsed.kind != "quiz" and (parsed.answer is not None or parsed.explanation is not None):
                raise ValueError("Only quiz sections can contain answer-key fields.")
            if modules and section.get("module_id") not in {m["id"] for m in outline["modules"]}:
                raise ValueError("Backup section refers to an unknown module.")
            sections.append({**parsed.model_dump(),"edited":True,"order":order,
                             "support_status":"needs_review","review_notes":[IMPORT_NOTE]})
        if len({s["id"] for s in sections}) != len(sections):
            raise ValueError("Backup contains duplicate section identifiers.")
        completed = []
        for module in outline.get("modules",[]):
            expected = Counter({kind:1 for kind in ("objectives","introduction","readings","notes","announcement")})
            expected.update(assignment=module["assignments"],rubric=module["assignments"],
                            quiz=module["quizzes"] * options.questions_per_quiz)
            actual = Counter(s["kind"] for s in sections if s.get("module_id") == module["id"])
            if actual == expected:
                completed.append(module["id"])
        course = {"id":uuid.uuid4().hex, "document_id":source_id,"title":options.title,
            "difficulty":options.difficulty,"mode":options.mode,
            "options":{key:getattr(options,key) for key in ("modules","assignments","quizzes","questions_per_quiz")},
            "outline":outline,"outline_approved":False,"status":"needs_review","sections":sections,
            "review_flags":[IMPORT_NOTE],"created_at":now(),"updated_at":now(),"version":1,"archived":False}
        if modules:
            course["generated_module_ids"] = completed
        document = {"id":source_id,"filename":filename,"sha256":digest,"format":file_format,
                    "ocr_pages":ocr_pages,"created_at":now(),"passages":[],"source_references":references,
                    "warnings":["Original source is missing. Reattach the matching file to inspect evidence or regenerate."],
                    "is_sample":False,"source_missing":True}
        return course, document
    except (KeyError, TypeError, AttributeError, ValueError, RecursionError) as exc:
        raise ValueError("Invalid course backup. Choose an unmodified Easy Street JSON export.") from exc


def install_workspace_routes(app, service):
    def get_course(course_id):
        course = service.store.get("courses", course_id)
        if not course:
            raise HTTPException(404,"Course not found.")
        return course

    def editable(course_id):
        if service.active(course_id):
            raise HTTPException(409,"Wait for or cancel the active generation job first.")

    @app.post("/api/courses/import")
    async def import_course(file: UploadFile = File(...)):
        try:
            course, source = parse_backup(await file.read(MAX_BACKUP + 1))
        finally:
            await file.close()
        with service.lock:
            existing = service.store.get("documents", source["id"])
            if existing and existing["sha256"] != source["sha256"]:
                raise HTTPException(409,"Backup source identity conflicts with a saved document.")
            if not existing:
                service.store.put_document(source)
            course["source_missing"] = not bool(existing and existing.get("passages"))
            service.store.put_course(course)
        return course

    @app.post("/api/courses/{id}/archive")
    def archive(id: str, state: ArchiveInput):
        with service.lock:
            course = get_course(id)
            editable(id)
            course["archived"] = state.archived
            service.store.put_course(course)
            return course

    @app.post("/api/courses/{id}/restore")
    def restore(id: str, request: RestoreInput):
        with service.lock:
            current = get_course(id)
            editable(id)
            version = next((v for v in service.store.histories(id) if v["id"] == request.version_id),None)
            if not version:
                raise HTTPException(404,"Saved version not found for this course.")
            course = copy.deepcopy(version["course"])
            course["id"] = id
            course["archived"] = current.get("archived",False)
            source = service.store.get("documents",course["document_id"])
            course["source_missing"] = not bool(source and source.get("passages"))
            course["status"] = "needs_review" if course["sections"] else "outline"
            course["outline_approved"] = False
            service.store.put_course(course,"Before restoring a saved version")
            return course

    @app.post("/api/courses/{id}/source")
    async def attach_source(id: str, file: UploadFile = File(...)):
        from .extraction import MAX_UPLOAD
        try:
            data = await file.read(MAX_UPLOAD + 1)
        finally:
            await file.close()
        with service.lock:
            course = get_course(id)
            editable(id)
            source = service.store.get("documents",course["document_id"])
            if not source or hashlib.sha256(data).hexdigest() != source["sha256"]:
                raise HTTPException(422,"Choose the exact original file named in this course backup.")
            restored = service.document(data,source["filename"],ocr_pages=source.get("ocr_pages") or None)
            if not restored.get("passages") or restored["id"] != source["id"]:
                raise HTTPException(422,"This source extraction differs from the backup. Create a new course from its preview.")
            # Reconnecting a source also repairs other imported courses sharing it.
            for related in service.store.all("courses"):
                if related["document_id"] == source["id"] and related.get("source_missing"):
                    related["source_missing"] = False
                    service.store.put_course(related)
            return get_course(id)
