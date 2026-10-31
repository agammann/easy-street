import hashlib
import json
import threading
import uuid
from pathlib import Path
from .demo import DEMO_VERSION, demo_course, demo_module
from .extraction import extract
from .grounding import ground_sections, validate_structure
from .models import GeneratedCourse, Verification
from .planning import course_modules, module_passages, propose_modules, sync_outline
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

    def document(self, data, filename, ocr_pages=None):
        digest = hashlib.sha256(data).hexdigest()
        existing = self.store.get("documents",digest[:24]) if not ocr_pages else None
        if existing and not existing.get("source_missing"):
            return {**existing,"cached":True}
        value = extract(data,filename,ocr_pages=ocr_pages,allow_ocr_preview=True)
        existing = self.store.get("documents",value["id"])
        if existing and not existing.get("source_missing"):
            return {**existing,"cached":True}
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
        if document.get("source_missing") or document.get("insufficient_text") or not document["passages"]:
            raise ValueError("This source needs more readable text before course creation. Select pages for local OCR or upload a readable document.")
        if options.mode == "demo" and not document["is_sample"]:
            raise ValueError("Offline demo can only use the included original sample.")
        course = {"id":uuid.uuid4().hex,"document_id":document["id"],"title":options.title,"difficulty":options.difficulty,
            "mode":options.mode,"options":{k:getattr(options,k) for k in ("modules","assignments","quizzes","questions_per_quiz")},
            "outline":{"title":options.title,"modules":propose_modules(document,options)},
            "outline_approved":False,"status":"outline","sections":[],"review_flags":[],"created_at":now(),"updated_at":now(),"version":1}
        sync_outline(course,document)
        self.store.put_course(course)
        return course

    def edit_outline(self,course,changes):
        document = self.store.get("documents",course["document_id"])
        if not document:
            raise ValueError("Reattach the source document before changing this outline.")
        modules = course_modules(course)
        if "modules" in changes:
            # Generated courses retain structural membership; their section edits are
            # preserved. Change source scope only before generating the first module.
            if course["sections"]:
                for old,new in zip(modules,changes["modules"]):
                    if any(old[key] != new[key] for key in ("id","assignments","quizzes","selected_passage_ids")):
                        raise ValueError("After generation, keep each module's sources and assessment distribution. Create a new course for a different structure.")
            modules = changes["modules"]
        if "module_title" in changes:
            modules[0]["title"] = changes["module_title"]
        if "objectives" in changes:
            modules[0]["objectives"] = changes["objectives"]
        course["outline"].update(modules=modules)
        if "title" in changes:
            course["title"] = changes["title"]
            course["outline"]["title"] = changes["title"]
        sync_outline(course,document)
        return course

    def active(self, course_id):
        return next((j for j in self.store.all("jobs") if j["course_id"] == course_id and j["status"] in ("queued","running","interrupted")),None)

    def payload(self, course, section_id=None, module_id=None):
        document = self.store.get("documents",course["document_id"])
        if not document:
            raise ValueError("Reattach the original source document before generation.")
        target = next((s for s in course["sections"] if s["id"] == section_id),None) if section_id else None
        if section_id and not target:
            raise ValueError("Section not found.")
        modules = course_modules(course)
        module_id = (target.get("module_id") or modules[0]["id"]) if target else (module_id or modules[0]["id"])
        module = next((m for m in modules if m["id"] == module_id),None)
        if module is None:
            raise ValueError("Module not found.")
        selected = module_passages(document,module)
        if target and target["evidence"]:
            ids = {e["passage_id"] for e in target["evidence"]}
            subset = [p for p in selected if p["id"] in ids]
            if subset:
                selected = subset
        return {"prompt_version":PROMPT_VERSION,"course_title":course["title"],"difficulty":course["difficulty"],
                "options":{**course["options"],"modules":1,"assignments":module["assignments"],"quizzes":module["quizzes"]},
                "course_options":course["options"],"module":module,
                "outline":{"title":course["title"],"module_title":module["title"],"objectives":module["objectives"]},
                "target_section":{"id":target["id"],"kind":target["kind"]} if target else None,"passages":selected}

    def pending_modules(self,course,section_id=None):
        modules = course_modules(course)
        if section_id:
            target = next((s for s in course["sections"] if s["id"] == section_id),None)
            if not target:
                raise ValueError("Section not found.")
            return [next(m for m in modules if m["id"] == (target.get("module_id") or modules[0]["id"]))]
        completed = course.get("generated_module_ids", [])
        return [m for m in modules if m["id"] not in completed]

    def estimate(self, course, section_id=None):
        if course.get("archived"):
            raise ValueError("Restore this course from the archive before generating content.")
        document = self.store.get("documents",course["document_id"])
        if not document or document.get("source_missing") or course.get("source_missing"):
            raise ValueError("Reattach the original source document before estimating generation.")
        estimates = []
        for module in self.pending_modules(course,section_id):
            payload = self.payload(course,section_id,module["id"])
            value = estimate(payload,bool(section_id),module_passages(document,module))
            cached = self.store.cache_get(self.cache_key(course,payload)) is not None
            if course["mode"] == "demo" or cached:
                value.update(estimated_max_usd=0,input_tokens_estimate=0,output_tokens_limit=0)
            estimates.append({**value,"module_id":module["id"],"cached":cached})
        if not estimates:
            raise ValueError("This course already has all modules. Choose an individual section to regenerate.")
        value = {**estimates[0],"modules":estimates}
        for key in ("estimated_max_usd","input_tokens_estimate","output_tokens_limit"):
            value[key] = round(sum(item[key] for item in estimates),8)
        value["provider_calls_max"] = 0 if course["mode"] == "demo" else sum(2 for item in estimates if not item["cached"])
        if all(item["cached"] for item in estimates):
            value["notice"] = "The saved generation and evidence review will be reused locally. No new provider calls or charges are required."
        value["budget"] = self.store.budget()
        return value

    def cache_key(self,course,payload):
        identity = {"payload":payload,"model":MODEL,"mode":course["mode"]}
        target = payload.get("target_section")
        if target:
            saved = next((s for s in course["sections"] if s["id"] == target["id"]),None)
            if not saved or saved["kind"] != target["kind"]:
                raise ValueError("Section not found.")
            # Keep edit-sensitive cache behavior without sending saved section data
            # or its digest to the provider or exposing it in an estimate.
            identity["target_snapshot"] = hashlib.sha256(json.dumps(saved,sort_keys=True).encode()).hexdigest()
        if course["mode"] == "demo":
            identity["demo_version"] = DEMO_VERSION
        return hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()

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
            if course["sections"] and not request.section_id and (not course.get("generated_module_ids") or not self.pending_modules(course)):
                raise ValueError("This course already has saved sections. Regenerate an individual section to preserve your edits.")
            modules = self.pending_modules(course,request.section_id)
            value = self.estimate(course,request.section_id)
            if course["mode"] == "openai" and not self.key_configured and value["provider_calls_max"]:
                raise ValueError("Configure OPENAI_API_KEY in the backend environment before generation.")
            maximum = value["estimated_max_usd"]
            job = {"id":uuid.uuid4().hex,"course_id":course_id,"section_id":request.section_id,"status":"queued","stage":"queued",
                "error":None,"created_at":now(),"updated_at":now(),"estimated_max_usd":maximum,"cancel_requested":False,
                "module_ids":[m["id"] for m in modules],"total_modules":len(modules),"completed_modules":0,"current_module_id":modules[0]["id"]}
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
        with self.lock:
            self.job_stage(job,"cancelled")
            job["status"] = "cancelled"
            self.store.put_job(job,release=True)
            course = self.store.get("courses",job["course_id"])
            course["status"] = "needs_review" if course["sections"] else "ready"
            self.store.put_course(course)

    def begin_provider_call(self,job,stage):
        with self.lock:
            if self.store.get("jobs",job["id"])["cancel_requested"]:
                self.finish_cancel(job)
                return False
            self.job_stage(job,stage)
            return True

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
        try:
            course = self.store.get("courses",job["course_id"])
            document = self.store.get("documents",course["document_id"])
            modules = course_modules(course)
            module_ids = job.get("module_ids") or [m["id"] for m in self.pending_modules(course,job["section_id"])]
            job.setdefault("module_results",{})
            job.update(total_modules=len(module_ids),completed_modules=0)
            for module_id in module_ids:
                course = self.store.get("courses",job["course_id"])
                if not job["section_id"] and module_id in course.get("generated_module_ids",[]):
                    job["completed_modules"] += 1
                    continue
                module = next(m for m in modules if m["id"] == module_id)
                job["current_module_id"] = module_id
                self.job_stage(job,"preparing")
                if self.store.get("jobs",job_id)["cancel_requested"]:
                    self.finish_cancel(job)
                    return
                payload = self.payload(course,job["section_id"],module_id)
                key = self.cache_key(course,payload)
                cache = self.store.cache_get(key)
                checkpoint = job["module_results"].setdefault(module_id,{})
                # Existing single-module interrupted jobs keep their old checkpoint keys.
                if len(module_ids) == 1:
                    for field in ("generated","verification"):
                        if field in job:
                            checkpoint.setdefault(field,job[field])
                if cache is not None:
                    generated = GeneratedCourse.model_validate(cache["generated"])
                    verification = Verification.model_validate(cache["verification"])
                elif course["mode"] == "demo":
                    if len(modules) == 1 and module["assignments"] == module["quizzes"] == 1 and len(payload["passages"]) == len(document["passages"]):
                        generated, verification = demo_course(document,course["options"]["questions_per_quiz"],job["section_id"])
                    else:
                        generated, verification = demo_module(document,payload)
                else:
                    if "generated" in checkpoint:
                        generated = GeneratedCourse.model_validate(checkpoint["generated"])
                    else:
                        self.store.ensure_call_budget(job_id,cost(UsageCounts(generation_input_bound(payload),MAX_GENERATION_TOKENS)))
                        if not self.begin_provider_call(job,"generation_in_flight"):
                            return
                        generated, usage = self.provider.generate(payload)
                        self.store.usage(job_id,"generation",MODEL,usage,cost(usage))
                        checkpoint["generated"] = generated.model_dump()
                        self.job_stage(job,"generation_received")
                    validate_structure(generated,course["options"]["questions_per_quiz"],payload["target_section"],module["assignments"],module["quizzes"])
                    if self.store.get("jobs",job_id)["cancel_requested"]:
                        self.finish_cancel(job)
                        return
                    # The review sees every approved passage in this module, including
                    # conflicts outside the target section's narrower generation scope.
                    validation_payload = {"passages":module_passages(document,module),"sections":generated.model_dump()["sections"]}
                    if "verification" in checkpoint:
                        verification = Verification.model_validate(checkpoint["verification"])
                    else:
                        self.store.ensure_call_budget(job_id,cost(UsageCounts(verification_input_bound(validation_payload),MAX_VERIFICATION_TOKENS)))
                        if not self.begin_provider_call(job,"verification_in_flight"):
                            return
                        verification, usage = self.provider.verify(validation_payload)
                        self.store.usage(job_id,"verification",MODEL,usage,cost(usage))
                        checkpoint["verification"] = verification.model_dump()
                        self.job_stage(job,"verification_received")
                validate_structure(generated,course["options"]["questions_per_quiz"],payload["target_section"],module["assignments"],module["quizzes"])
                sections = ground_sections(generated,payload["passages"],verification)
                self.store.cache_put(key,{"generated":generated.model_dump(),"verification":verification.model_dump()})
                with self.lock:
                    if self.store.get("jobs",job_id)["cancel_requested"]:
                        self.finish_cancel(job)
                        return
                    course = self.store.get("courses",job["course_id"])
                    if job["section_id"]:
                        old = next(s for s in course["sections"] if s["id"] == job["section_id"])
                        sections[0].update(order=old["order"],module_id=old.get("module_id",module_id),assessment_id=old.get("assessment_id"))
                        course["sections"] = [sections[0] if s["id"] == job["section_id"] else s for s in course["sections"]]
                        if old["kind"] in ("notes","introduction","objectives","readings"):
                            for section in course["sections"]:
                                if section["kind"] in ("assignment","quiz") and section.get("module_id",module_id) == module_id:
                                    section["support_status"] = "needs_review"
                                    section["review_notes"] = list(dict.fromkeys(section["review_notes"] + ["A related learning section changed; review this assessment for consistency."]))
                    else:
                        canonical_ids = len(modules) > 1 or module["assignments"] != 1 or module["quizzes"] != 1
                        counts = {}
                        for section in sections:
                            kind = section["kind"]
                            counts[kind] = counts.get(kind,0)+1
                            section["module_id"] = module_id
                            if canonical_ids:
                                section["id"] = f"{module_id}-{kind}-{counts[kind]}"
                            if kind in ("assignment","rubric"):
                                section["assessment_id"] = f"{module_id}-assignment-{counts[kind]}"
                            elif kind == "quiz":
                                section["assessment_id"] = f"{module_id}-quiz-{(counts[kind]-1)//course['options']['questions_per_quiz']+1}"
                            section["order"] += len(course["sections"])
                        course["sections"].extend(sections)
                        course["generated_module_ids"] = list(dict.fromkeys(course.get("generated_module_ids",[])+[module_id]))
                    refresh_review(course)
                    course["status"] = "generating"
                    self.store.put_course(course,"Before section regeneration" if job["section_id"] else f"Before generating {module_id}")
                    job["completed_modules"] += 1
                    self.job_stage(job,"module_complete")
            with self.lock:
                course = self.store.get("courses",job["course_id"])
                refresh_review(course)
                self.store.put_course(course)
                job.update(status="complete",stage="complete",updated_at=now())
                self.store.put_job(job,release=True)
        except Exception:
            # Never return raw provider errors, which may contain source text or credentials.
            with self.lock:
                uncertain = job["stage"].endswith("_in_flight")
                job.update(status="uncertain" if uncertain else "failed",updated_at=now(),
                    error=("Provider completion or billing is uncertain. No automatic retry was made; the remaining maximum cost stays reserved. Check provider usage before starting a new request." if uncertain else
                           "Generation stopped safely because output validation or the next-step budget check failed. No automatic retry was made. Review your source and options before a new request."))
                self.store.put_job(job,release=not uncertain)
                if uncertain:
                    self.store.usage(job_id,job["stage"],MODEL,UsageCounts(0,0),0,"uncertain")
                course = self.store.get("courses",job["course_id"])
                course["status"] = "error"
                self.store.put_course(course)


def refresh_review(course):
    course["review_flags"] = [f"{s['title']}: {note}" for s in course["sections"] for note in s["review_notes"]]
    course["status"] = "needs_review" if course["review_flags"] else "complete"
