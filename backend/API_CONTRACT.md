# Easy Street API contract

Base `/api`. JSON responses except uploads and exports. Errors are `{detail: string}`. Endpoints are local only. Allowed frontend origins are localhost/127.0.0.1 on ports 8000 and 5173. The backend serves `frontend/dist` when built. IDs are strings. Source text is untrusted data and must always render as text.

## Setup and documents

- `GET /health` → `{status:"ok"}`.
- `GET /config` → provider/model/key-configured indicator, pricing, cumulative budget, privacy notice, `limits:{modules:6,assignments:6,quizzes:6,max_questions:5,assignments_per_module:2,quizzes_per_module:2,source_chars_per_module:24000}` and `ocr:{available,reason,max_pages:5,language:"eng"}`. The legacy `milestone` limits remain available. No secret is returned.
- `POST /documents` multipart `file` (PDF, DOCX, UTF-8 TXT; 15 MiB maximum) and optional `ocr_pages` (a JSON array of one to five distinct page numbers) → Document. OCR is local, English, explicit and PDF-only. OCR variants have distinct IDs while retaining the original file digest. Repeat extraction with the same options and output reuses the same document.
- `POST /documents/sample` → the original sample Document, eligible for Offline demo.
- `GET /documents/{id}` → Document; `GET /documents` → summaries without passage text.

Document: `{id,filename,sha256,format:"pdf"|"docx"|"txt",created_at,passages:Passage[],warnings:string[],is_sample:boolean,page_count?:number|null,ocr_pages:number[],needs_ocr_pages:number[],insufficient_text:boolean,cached?:boolean,source_missing?:boolean}`.

Passage: `{id,document_id,text,location,page:number|null,paragraph:number,heading,ocr?:boolean}`. PDF locations use actual page numbers. TXT/DOCX locations use paragraph numbers, never inferred pages. Sources are bounded to 100 PDF pages and 250,000 extracted characters; course creation requires at least 150 readable characters. A scanned PDF can return a preview with no passages and `insufficient_text:true`; it cannot create a course until enough text is extracted. Imported backups can create a missing-source Document with `source_references` containing locations but no source text.

## Course planning

- `POST /courses` accepts `{document_id,title,difficulty:"introductory"|"intermediate"|"advanced",modules:1..6,assignments:0..6,quizzes:0..6,questions_per_quiz:1..5,mode:"demo"|"openai"}` → Course. Assignment and quiz totals are course-wide, each at most twice the number of modules. The source needs at least as many passages as modules. Planning is deterministic and free. Offline demo accepts only the included original sample.
- `GET /courses` → Course[], including archived courses. `GET /courses/{id}` → Course.
- `PATCH /courses/{id}/outline` accepts `{title?,modules?:OutlineModule[],module_title?,objectives?}` → Course, saves the previous version and revokes approval. The legacy `module_title` and `objectives` fields update the first module. A modules update supplies the entire array in its original order. Counts must add up to the course options. Each module needs distinct IDs from its source document, at most 24,000 characters. After any generation, its source selections and assessment distribution are fixed; title/objective edits remain allowed and mark saved content for review.
- `POST /courses/{id}/approve` accepts `{provider_disclosure_accepted:true}` → Course.

OutlineModule: `{id:"module-1".."module-6",title,objectives:string[],selected_passage_ids:string[],assignments:0..2,quizzes:0..2}`.

The planner partitions the entire document in source order, including later passages. If a partition exceeds 24,000 characters or 512 actual evidence excerpts, it selects passages throughout that span and explicitly warns about omitted coverage. The outline records the exact selection for review. Each module may have at most two assignments, two rubrics and ten quiz questions, plus five learning sections (19 sections total). The proposed syllabus and course objectives derive from the approved module plan, without another provider call.

Course includes `{id,document_id,title,difficulty,mode,options,outline,outline_approved,status,sections,review_flags,created_at,updated_at,version,generated_module_ids?:string[],archived?:boolean,source_missing?:boolean}`. Status is `outline|ready|generating|complete|needs_review|error`. Outline contains `title,modules,course_objectives,distribution,warnings,selected_passage_ids` and the first-module compatibility fields `module_title,objectives`.

## Generation and recovery

- `GET /courses/{id}/estimate?section_id=...` → `{estimated_max_usd,input_tokens_estimate,output_tokens_limit,verification_included:true,pricing,budget,notice,provider_calls_max,modules:[{module_id,cached,...}]}`. Estimates sum only unfinished modules or the targeted section. Cached results and Offline demo cost zero; cached generation needs no configured key.
- `POST /courses/{id}/generate` accepts `{idempotency_key,section_id?:string}` → Job. Requires approval. Without a section ID it generates unfinished modules in order, saving each complete module before proceeding. After cancellation or a safe failure, a new approved request can finish the remaining modules without replacing saved ones. Once all modules exist, regenerate one section at a time. Duplicate request IDs return the original Job; concurrent jobs are rejected.
- `GET /courses/{id}/job` → latest public Job or `null`. Recover progress from this endpoint on reload.
- `GET /jobs/{id}` → Job.
- `POST /jobs/{id}/cancel` → Job. Cancellation is sticky and checked before each provider dispatch. An in-flight call may still incur a charge. Completed modules remain saved.
- `POST /jobs/{id}/resume` → Job. Only interrupted jobs without an in-flight or uncertain request can resume. Persisted generation/verification results and completed modules are reused. No automatic paid retries occur.

Job: `{id,course_id,section_id:string|null,status:"queued"|"running"|"complete"|"failed"|"uncertain"|"cancelled"|"interrupted",stage,error:string|null,created_at,updated_at,estimated_max_usd,cancel_requested,module_ids:string[],total_modules,completed_modules,current_module_id}`. Module counts refer to this request's `module_ids`, not the entire course. Stage is `queued|preparing|generation_in_flight|generation_received|verification_in_flight|verification_received|module_complete|complete|cancelled`. Public jobs omit saved provider outputs and internal module checkpoints.

Each uncached module makes one generation and one independent evidence-review request. Targeted regeneration uses source passages from that section's module; its independent review sees the module's complete approved source selection. Billing uncertainty leaves the remaining maximum reserved and prevents automatic replay. Budget is cumulative per local database, not per course or per day.

## Editing, versions and files

- `PATCH /courses/{id}/sections/{section_id}` accepts `{title?,body?,answer?,explanation?}` → Course, saves the prior version and marks manual edits for review. Non-quiz sections cannot have answer fields. Learning edits mark that module's dependent assessments for review.
- `POST /courses/{id}/reorder` accepts `{section_ids:string[]}` → Course. Every section ID is required exactly once.
- `GET /courses/{id}/versions` → `{id,created_at,reason,course}[]`.
- `POST /courses/{id}/restore` accepts `{version_id:number}` → Course, saves the current version before restoring and revokes approval.
- `POST /courses/{id}/archive` accepts `{archived:boolean}` → Course. Archive is reversible; active jobs must finish or be canceled first. Archived courses cannot generate.
- `GET /courses/{id}/export?format=html|answers|json` → learner HTML with proposed syllabus and module grouping, separate answer HTML, or `easy-street-course-v1` JSON. Original source passages/files are excluded; short evidence quotes and source locations remain. Exports require saved sections.
- `POST /courses/import` multipart `file` (Easy Street JSON, at most 15 MiB) → a new Course. Imports never overwrite an existing course, always require review and revoke approval. Existing matching source material is reused; otherwise read/edit/export works with source references only. Completed-module markers are reconstructed so continuing a partial backup preserves completed work.
- `POST /courses/{id}/source` multipart `file` → Course. Reattaches the exact original file by digest and extraction identity; OCR selections from the backup are reused. Missing-source courses cannot estimate or generate until reattached.
- `GET /usage` → `{budget,records:Usage[]}`.

Section: `{id,kind:"objectives"|"introduction"|"readings"|"notes"|"announcement"|"assignment"|"rubric"|"quiz",title,body,answer:string|null,explanation:string|null,evidence:Evidence[],support_status:"supported"|"needs_review"|"proposal",review_notes:string[],edited:boolean,order,module_id?:string|null,assessment_id?:string|null}`. There is one quiz section per question. `assessment_id` groups quiz questions and pairs assignment/rubric sections. Older single-module sections may lack membership metadata. Learner views must hide answers, explanations and potentially revealing quiz evidence quotes. Course mode `demo` must be visibly labeled **Offline demo**.

Evidence is `{passage_id,quote}`. Quotes must resolve to exact source substrings; an exact quote alone does not prove a generated claim. Structural proposals stay labeled even when evidence review raises a flag. Model support judgments are fallible and require human review.

Usage is `{id,job_id,stage,model,input_tokens,output_tokens,cost_usd,status:"completed"|"uncertain",created_at}`.

The server entry point is `backend.app:app`. Import `backend.main.create_app` for isolated tests; importing the factory does not load environment files or open a default database. Run one server process per data directory so restart recovery belongs to that instance.
