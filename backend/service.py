import hashlib
import json
import threading
import uuid
from pathlib import Path
from .demo import demo_course
from .extraction import extract, select_passages
from .grounding import ground_sections, validate_structure
from .models import GeneratedCourse, Verification
from .provider import (MODEL, PROMPT_VERSION, MAX_GENERATION_TOKENS, MAX_VERIFICATION_TOKENS,
                       UsageCounts, OpenAIProvider, cost, estimate, generation_input_bound, verification_input_bound)
from .store import Store, now


class Service:
    def __init__(self, data_dir: Path, budget_limit: float, provider=None):
        self.data_dir = data_dir
        self.store = Store(data_dir / "easy-street.sqlite3",budget_limit)
        self.provider = provider or OpenAIProvider()
        self.key_configured = provider is not None or bool(self.provider.api_key)
        self.lock = threading.RLock()
        self.recover()

    def recover(self):
        for job in self.store.all("jobs"):
            if job["status"] in ("queued","running"):
                if job["stage"].endswith("_in_flight"):
                    job.update(status="uncertain",error="The application restarted while a provider request was in flight. Billing or completion may be uncertain. This request will not be automatically repeated.")
                else:
                    job.update(status="interrupted",error="The application restarted before the next provider request. This job can safely resume.")
                job["updated_at"] = now()
                self.store.put_job(job)
                course = self.store.get("courses",job["course_id"])
                if course:
                    course["status"] = "error"
                    self.store.put_course(course)

    def document(self, data, filename):
        digest = hashlib.sha256(data).hexdigest()
        existing = self.store.get("documents",digest[:24])
        if existing:
            return {**existing,"cached":True}
        value = extract(data,filename)
        value["created_at"] = now()
        original = self.data_dir / "originals" / (value["sha256"] + "." + value["format"])
        original.parent.mkdir(parents=True,exist_ok=True)
        original.write_bytes(data)
        self.store.put_document(value)
        return {**value,"cached":False}

    def create_course(self, options):
        document = self.store.get("documents",options.document_id)
        if not document:
            raise ValueError("Document not found.")
        if options.mode == "demo" and not document["is_sample"]:
            raise ValueError("Offline demo can only use the included original sample.")
        selected = select_passages(document)
        headings = [p["heading"] for p in selected if len(p["heading"]) < 100][:5]
        warnings = list(document["warnings"])
        if len(selected) != len(document["passages"]):
            warnings.append(f"This milestone uses the first {len(selected)} of {len(document['passages'])} extracted passages (up to 24,000 characters). Content outside those passages is not covered.")
        if len(selected) < options.questions_per_quiz:
            warnings.append("Requested questions exceed distinct passages. Reduce the question count if the outline repeats coverage.")
        course = {"id":uuid.uuid4().hex,"document_id":document["id"],"title":options.title,"difficulty":options.difficulty,
            "mode":options.mode,"options":{k:getattr(options,k) for k in ("modules","assignments","quizzes","questions_per_quiz")},
            "outline":{"title":options.title,"module_title":headings[0] if headings else "Explore the supplied chapter",
                "objectives":[f"Examine {h}." for h in headings[:3]] or ["Explain the ideas in the selected passages."],
                "distribution":[{"module":1,"assignments":1,"quizzes":1,"questions":options.questions_per_quiz}],
                "warnings":warnings,"selected_passage_ids":[p["id"] for p in selected]},
            "outline_approved":False,"status":"outline","sections":[],"review_flags":[],"created_at":now(),"updated_at":now(),"version":1}
        self.store.put_course(course)
        return course

    def active(self, course_id):
        return next((j for j in self.store.all("jobs") if j["course_id"] == course_id and j["status"] in ("queued","running","interrupted")),None)

    def payload(self, course, section_id=None):
        document = self.store.get("documents",course["document_id"])
        target = next((s for s in course["sections"] if s["id"] == section_id),None) if section_id else None
        if section_id and not target:
            raise ValueError("Section not found.")
        selected = select_passages(document)
        if target and target["evidence"]:
            ids = {e["passage_id"] for e in target["evidence"]}
            subset = [p for p in selected if p["id"] in ids]
            if subset:
                selected = subset
        return {"prompt_version":PROMPT_VERSION,"course_title":course["title"],"difficulty":course["difficulty"],
                "options":course["options"],"outline":course["outline"],"target_section":target,"passages":selected}

    def estimate(self, course, section_id=None):
        document = self.store.get("documents",course["document_id"])
        value = estimate(self.payload(course,section_id),bool(section_id),select_passages(document))
        if course["mode"] == "demo":
            value.update(estimated_max_usd=0,input_tokens_estimate=0,output_tokens_limit=0)
        value["budget"] = self.store.budget()
        return value

    def submit(self, course_id, request):
        with self.lock:
            course = self.store.get("courses",course_id)
            if not course:
                raise ValueError("Course not found.")
            # Resolve idempotency before any state-dependent validation.
            with self.store.connect() as db:
                row = db.execute("SELECT data FROM jobs WHERE idem=?",(request.idempotency_key,)).fetchone()
            if row:
                existing = json.loads(row[0])
                if existing["course_id"] != course_id or existing["section_id"] != request.section_id:
                    raise ValueError("This idempotency key belongs to another generation request.")
                return existing, False
            if not course["outline_approved"]:
                raise ValueError("Approve the outline and provider disclosure before generation.")
            if self.active(course_id):
                raise ValueError("A generation job is already active for this course.")
            if course["sections"] and not request.section_id:
                raise ValueError("This course already has saved sections. Regenerate an individual section to preserve your edits.")
            if course["mode"] == "openai" and not self.key_configured:
                raise ValueError("Configure OPENAI_API_KEY in the backend environment before generation.")
            maximum = self.estimate(course,request.section_id)["estimated_max_usd"]
            job = {"id":uuid.uuid4().hex,"course_id":course_id,"section_id":request.section_id,"status":"queued","stage":"queued",
                "error":None,"created_at":now(),"updated_at":now(),"estimated_max_usd":maximum,"cancel_requested":False}
            existing = self.store.reserve_job(job,request.idempotency_key,maximum)
            if existing:
                return existing,False
            course["status"] = "generating"
            self.store.put_course(course)
            return job,True

    def job_stage(self, job, stage):
        latest = self.store.get("jobs",job["id"])
        job["cancel_requested"] = latest["cancel_requested"]
        job.update(stage=stage,updated_at=now())
        self.store.put_job(job)

    def finish_cancel(self, job):
        self.job_stage(job,"cancelled")
        job["status"] = "cancelled"
        self.store.put_job(job,release=True)
        course = self.store.get("courses",job["course_id"])
        course["status"] = "needs_review" if course["sections"] else "ready"
        self.store.put_course(course)

    def run(self, job_id):
        with self.lock:
            job = self.store.get("jobs",job_id)
            if not job or job["status"] != "queued":
                return
            if job["cancel_requested"]:
                self.finish_cancel(job)
                return
            job["status"] = "running"
            self.job_stage(job,"preparing")
        course = self.store.get("courses",job["course_id"])
        document = self.store.get("documents",course["document_id"])
        payload = self.payload(course,job["section_id"])
        key = hashlib.sha256(json.dumps({"payload":payload,"model":MODEL,"mode":course["mode"]},sort_keys=True).encode()).hexdigest()
        cache = self.store.cache_get(key)
        try:
            if cache:
                generated = GeneratedCourse.model_validate(cache["generated"])
                verification = Verification.model_validate(cache["verification"])
            elif course["mode"] == "demo":
                generated, verification = demo_course(document,course["options"]["questions_per_quiz"],job["section_id"])
            else:
                if "generated" in job:
                    generated = GeneratedCourse.model_validate(job["generated"])
                else:
                    self.store.ensure_call_budget(job_id,cost(UsageCounts(generation_input_bound(payload),MAX_GENERATION_TOKENS)))
                    self.job_stage(job,"generation_in_flight")
                    generated, usage = self.provider.generate(payload)
                    self.store.usage(job_id,"generation",MODEL,usage,cost(usage))
                    # Persist returned output before moving to the next provider call.
                    job["generated"] = generated.model_dump()
                    self.job_stage(job,"generation_received")
                validate_structure(generated,course["options"]["questions_per_quiz"],payload["target_section"])
                if self.store.get("jobs",job_id)["cancel_requested"]:
                    self.finish_cancel(job)
                    return
                # The independent review retains the whole bounded chapter context, including
                # potentially conflicting passages omitted from a targeted generation request.
                validation_payload = {"passages":select_passages(document),"sections":generated.model_dump()["sections"]}
                if "verification" in job:
                    verification = Verification.model_validate(job["verification"])
                else:
                    self.store.ensure_call_budget(job_id,cost(UsageCounts(verification_input_bound(validation_payload),MAX_VERIFICATION_TOKENS)))
                    self.job_stage(job,"verification_in_flight")
                    verification, usage = self.provider.verify(validation_payload)
                    self.store.usage(job_id,"verification",MODEL,usage,cost(usage))
                    job["verification"] = verification.model_dump()
                    self.job_stage(job,"verification_received")
            validate_structure(generated,course["options"]["questions_per_quiz"],payload["target_section"])
            sections = ground_sections(generated,payload["passages"],verification)
            self.store.cache_put(key,{"generated":generated.model_dump(),"verification":verification.model_dump()})
            with self.lock:
                if self.store.get("jobs",job_id)["cancel_requested"]:
                    self.finish_cancel(job)
                    return
                course = self.store.get("courses",job["course_id"])
                if job["section_id"]:
                    old = next(s for s in course["sections"] if s["id"] == job["section_id"])
                    sections[0]["order"] = old["order"]
                    course["sections"] = [sections[0] if s["id"] == job["section_id"] else s for s in course["sections"]]
                    if old["kind"] in ("notes","introduction","objectives","readings"):
                        for section in course["sections"]:
                            if section["kind"] in ("assignment","quiz"):
                                section["support_status"] = "needs_review"
                                section["review_notes"] = list(dict.fromkeys(section["review_notes"] + ["A related learning section changed; review this assessment for consistency."]))
                else:
                    course["sections"] = sections
                refresh_review(course)
                self.store.put_course(course,"Before section regeneration" if job["section_id"] else "Before first generation")
                job.update(status="complete",stage="complete",updated_at=now())
                self.store.put_job(job,release=True)
        except Exception:
            # Never return raw provider errors, which may contain source text or credentials.
            uncertain = job["stage"].endswith("_in_flight")
            job.update(status="uncertain" if uncertain else "failed",updated_at=now(),
                error=("Provider completion or billing is uncertain. No automatic retry was made; the remaining maximum cost stays reserved. Check provider usage before starting a new request." if uncertain else
                       "Generation stopped safely because output validation or the next-step budget check failed. No automatic retry was made. Review your source and options before a new request."))
            self.store.put_job(job,release=not uncertain)
            if uncertain:
                self.store.usage(job_id,job["stage"],MODEL,UsageCounts(0,0),0,"uncertain")
            course["status"] = "error"
            self.store.put_course(course)


def refresh_review(course):
    course["review_flags"] = [f"{s['title']}: {note}" for s in course["sections"] for note in s["review_notes"]]
    course["status"] = "needs_review" if course["review_flags"] else "complete"
