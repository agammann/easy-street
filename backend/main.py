import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from .extraction import MAX_UPLOAD, SAMPLE_PATH, ExtractionError
from .exports import export_course
from .grounding import proposal_title
from .models import CourseInput, OutlineEdit, Approval, GenerateInput, SectionEdit, ReorderInput
from .provider import MODEL, PRICING
from .service import Service, refresh_review
from .store import now

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local",override=False)
load_dotenv(ROOT / ".env",override=False)
ORIGINS = [f"http://{host}:{port}" for host in ("localhost","127.0.0.1") for port in (8000,5173)]


class BoundedRequestBody:
    """Enforce actual bytes before multipart parsing, including chunked requests."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in ("POST","PATCH","PUT"):
            return await self.app(scope,receive,send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body",b""))
            if len(body) > MAX_UPLOAD + 65536:
                response = JSONResponse({"detail":"Request exceeds the upload size limit."},status_code=413)
                return await response(scope,receive,send)
            if not message.get("more_body",False):
                break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type":"http.request","body":bytes(body),"more_body":False}
            return await receive()
        return await self.app(scope,bounded_receive,send)


def public_job(job):
    return {k:v for k,v in job.items() if k not in ("generated","verification")}


def create_app(data_dir: Path | None = None, provider=None, budget_limit: float | None = None):
    service = Service(Path(data_dir or os.environ.get("EASY_STREET_DATA_DIR",ROOT / "data")),
                      float(budget_limit if budget_limit is not None else os.environ.get("EASY_STREET_BUDGET_USD","1.00")),provider)
    app = FastAPI(title="Easy Street",version="0.1.0",docs_url="/api/docs",redoc_url=None)
    app.state.service = service
    app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_credentials=False,allow_methods=["GET","POST","PATCH"],allow_headers=["Content-Type"])
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=["localhost","127.0.0.1","[::1]"])
    app.add_middleware(BoundedRequestBody)

    @app.middleware("http")
    async def protect_local(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin not in ORIGINS:
            return JSONResponse({"detail":"This local application does not accept requests from that origin."},status_code=403)
        # Opening the app from another page can be a cross-site top-level navigation.
        # Only the static entry document may load that way; API requests remain blocked.
        frontend_navigation = (
            request.method == "GET"
            and request.url.path in ("/", "/index.html")
            and request.headers.get("sec-fetch-mode") == "navigate"
            and request.headers.get("sec-fetch-dest") == "document"
        )
        if request.headers.get("sec-fetch-site") == "cross-site" and not frontend_navigation:
            return JSONResponse({"detail":"Cross-site requests to the local application are blocked."},status_code=403)
        size = request.headers.get("content-length")
        if size:
            try:
                if int(size) > MAX_UPLOAD + 65536:
                    return JSONResponse({"detail":"Request exceeds the upload size limit."},status_code=413)
            except ValueError:
                return JSONResponse({"detail":"Invalid request size."},status_code=400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; frame-ancestors 'none'; base-uri 'self'"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ExtractionError)
    async def extraction_error(request, exc):
        return JSONResponse({"detail":str(exc)},status_code=400)

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return JSONResponse({"detail":str(exc)},status_code=400)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(request, exc):
        # FastAPI's default validation output includes rejected input values. Avoid reflecting
        # source excerpts or accidentally supplied secrets into browser errors and logs.
        return JSONResponse({"detail":"Invalid request fields. Check the course options and required text values."},status_code=422)

    def course_or_404(id):
        value = service.store.get("courses",id)
        if not value:
            raise HTTPException(404,"Course not found.")
        return value

    def job_or_404(id):
        value = service.store.get("jobs",id)
        if not value:
            raise HTTPException(404,"Job not found.")
        return value

    def editable(id):
        if service.active(id):
            raise HTTPException(409,"Wait for the active generation job before editing this course.")

    @app.get("/api/health")
    def health():
        return {"status":"ok"}

    @app.get("/api/config")
    def config():
        return {"provider":"openai","model":MODEL,"key_configured":service.key_configured,"pricing":PRICING,"budget":service.store.budget(),
            "milestone":{"modules":1,"assignments":1,"quizzes":1,"max_questions":5},
            "privacy_notice":"Original files and courses stay on this computer. OpenAI mode sends the selected excerpts to OpenAI for generation and a separate evidence review. Bring your own API key and pay OpenAI directly; the software is free. Use material you have permission to process. Application estimates are not a provider-enforced billing guarantee."}

    @app.post("/api/documents")
    async def upload(file: UploadFile = File(...)):
        # Bounded reads prevent holding an arbitrarily large uploaded body in application memory.
        data = await file.read(MAX_UPLOAD + 1)
        await file.close()
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413,"File exceeds the 15 MiB upload limit.")
        return service.document(data,file.filename or "upload")

    @app.post("/api/documents/sample")
    def sample():
        return service.document(SAMPLE_PATH.read_bytes(),"small-garden-watering.txt")

    @app.get("/api/documents")
    def documents():
        return [{k:v for k,v in d.items() if k != "passages"} for d in service.store.all("documents")]

    @app.get("/api/documents/{id}")
    def document(id: str):
        value = service.store.get("documents",id)
        if not value:
            raise HTTPException(404,"Document not found.")
        return value

    @app.post("/api/courses")
    def new_course(options: CourseInput):
        return service.create_course(options)

    @app.get("/api/courses")
    def courses():
        return service.store.all("courses")

    @app.get("/api/courses/{id}")
    def get_course(id: str):
        return course_or_404(id)

    @app.patch("/api/courses/{id}/outline")
    def outline(id: str, edit: OutlineEdit):
        with service.lock:
            course = course_or_404(id)
            editable(id)
            changes = edit.model_dump(exclude_none=True)
            course["outline"].update(changes)
            if "title" in changes:
                course["title"] = changes["title"]
            course.update(outline_approved=False,status="outline")
            for section in course["sections"]:
                section["support_status"] = "needs_review"
                section["review_notes"] = list(dict.fromkeys(section["review_notes"] + ["The course outline changed; review this saved section."]))
            service.store.put_course(course,"Before outline edit")
            return course

    @app.post("/api/courses/{id}/approve")
    def approve(id: str, approval: Approval):
        with service.lock:
            course = course_or_404(id)
            editable(id)
            course.update(outline_approved=True,status="ready" if not course["sections"] else "needs_review")
            service.store.put_course(course,"Before outline approval")
            return course

    @app.get("/api/courses/{id}/estimate")
    def estimate(id: str, section_id: str | None = None):
        return service.estimate(course_or_404(id),section_id)

    @app.post("/api/courses/{id}/generate")
    def generate(id: str, request: GenerateInput, background_tasks: BackgroundTasks):
        job,fresh = service.submit(id,request)
        if fresh:
            background_tasks.add_task(service.run,job["id"])
        return public_job(job)

    @app.get("/api/jobs/{id}")
    def get_job(id: str):
        return public_job(job_or_404(id))

    @app.post("/api/jobs/{id}/cancel")
    def cancel(id: str):
        with service.lock:
            job = job_or_404(id)
            if job["status"] in ("queued","running","interrupted"):
                job["cancel_requested"] = True
                service.store.put_job(job)
                if job["status"] in ("queued","interrupted"):
                    service.finish_cancel(job)
            return public_job(service.store.get("jobs",id))

    @app.post("/api/jobs/{id}/resume")
    def resume(id: str, background_tasks: BackgroundTasks):
        with service.lock:
            job = job_or_404(id)
            if job["status"] != "interrupted" or job["stage"].endswith("_in_flight"):
                raise HTTPException(409,"Only an interrupted job with no request in flight can resume. Uncertain requests are never automatically repeated.")
            job.update(status="queued",error=None,updated_at=now())
            service.store.put_job(job)
            background_tasks.add_task(service.run,id)
            return public_job(job)

    @app.patch("/api/courses/{id}/sections/{section_id}")
    def edit_section(id: str, section_id: str, edit: SectionEdit):
        with service.lock:
            course = course_or_404(id)
            editable(id)
            section = next((s for s in course["sections"] if s["id"] == section_id),None)
            if not section:
                raise HTTPException(404,"Section not found.")
            changes = edit.model_dump(exclude_unset=True)
            if any(changes.get(k) is None for k in ("title","body") if k in changes):
                raise HTTPException(422,"Title and body must contain text.")
            if section["kind"] != "quiz" and any(changes.get(k) is not None for k in ("answer","explanation")):
                raise HTTPException(422,"Only quiz sections have answer-key fields.")
            section.update(changes,edited=True,support_status="needs_review")
            section["title"] = proposal_title(section["kind"], section["title"])
            section["review_notes"] = list(dict.fromkeys(section["review_notes"] + ["Manually edited content needs a fresh source review."]))
            if section["kind"] in ("notes","introduction","objectives","readings"):
                for dependent in course["sections"]:
                    if dependent["kind"] in ("assignment","quiz"):
                        dependent["support_status"] = "needs_review"
                        dependent["review_notes"] = list(dict.fromkeys(dependent["review_notes"] + ["A related learning section changed; review this assessment for consistency."]))
            refresh_review(course)
            service.store.put_course(course,"Before manual section edit")
            return course

    @app.post("/api/courses/{id}/reorder")
    def reorder(id: str, order: ReorderInput):
        with service.lock:
            course = course_or_404(id)
            editable(id)
            existing = {s["id"] for s in course["sections"]}
            if len(order.section_ids) != len(existing) or set(order.section_ids) != existing:
                raise HTTPException(422,"Provide every section ID exactly once.")
            mapping = {s["id"]:s for s in course["sections"]}
            course["sections"] = [{**mapping[s],"order":i} for i,s in enumerate(order.section_ids)]
            service.store.put_course(course,"Before section reorder")
            return course

    @app.get("/api/courses/{id}/versions")
    def versions(id: str):
        course_or_404(id)
        return service.store.histories(id)

    @app.get("/api/courses/{id}/export")
    def export(id: str, format: str = "html"):
        if format not in ("html","answers","json"):
            raise HTTPException(422,"Choose html, answers, or json export.")
        course = course_or_404(id)
        if not course["sections"]:
            raise HTTPException(409,"Generate and review the course before exporting.")
        body,media,filename = export_course(course,format,service.store.get("documents",course["document_id"]))
        return Response(body,media_type=media,headers={"Content-Disposition":f'attachment; filename="{filename}"'})

    @app.get("/api/usage")
    def usage():
        return {"budget":service.store.budget(),"records":service.store.usage_records()}

    dist = ROOT / "frontend" / "dist"
    if dist.is_dir():
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets",StaticFiles(directory=assets),name="assets")
        @app.get("/{path:path}")
        def frontend(path: str):
            if path.startswith("api/"):
                raise HTTPException(404,"Endpoint not found.")
            asset = (dist / path).resolve()
            if asset.is_relative_to(dist.resolve()) and asset.is_file():
                return FileResponse(asset)
            return FileResponse(dist / "index.html")
    return app


app = create_app()
