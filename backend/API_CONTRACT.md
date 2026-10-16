# Easy Street API contract

Base `/api`. JSON responses except upload and exports. Errors `{detail: string}`. All endpoints are localhost-only. Development frontend origins localhost/127.0.0.1 port 5173; production port 8000. IDs are strings. The backend serves `frontend/dist` when built.

- `GET /health` → `{status:"ok"}`
- `GET /config` → `{provider:"openai",model:string,key_configured:boolean,pricing:{input_per_million:number,output_per_million:number,cached_input_per_million:number,updated:string},budget:{limit_usd:number,spent_usd:number,reserved_usd:number,remaining_usd:number},milestone:{modules:1,assignments:1,quizzes:1,max_questions:5},privacy_notice:string}`
- `POST /documents` multipart field `file` (PDF/TXT, max 15 MiB) → Document. Identical content returns cached same ID.
- `POST /documents/sample` → Document, the included original sample, eligible for offline demo.
- `GET /documents/{id}` → Document.
- `GET /documents` → DocumentSummary[].
- `POST /courses` JSON `{document_id,title,difficulty:"introductory"|"intermediate"|"advanced",modules:1,assignments:1,quizzes:1,questions_per_quiz:1..5,mode:"demo"|"openai"}` → Course. Builds a deterministic source-heading-based proposed outline; no paid call. Demo allowed only for original sample.
- `GET /courses` → Course[].
- `GET /courses/{id}` → Course.
- `PATCH /courses/{id}/outline` `{title?:string,module_title?:string,objectives?:string[]}` → Course; saves version and revokes approval.
- `POST /courses/{id}/approve` `{provider_disclosure_accepted:true}` → Course.
- `GET /courses/{id}/estimate?section_id=...` → `{estimated_max_usd:number,input_tokens_estimate:number,output_tokens_limit:number,verification_included:true,pricing:object,budget:object,notice:string}`.
- `POST /courses/{id}/generate` `{idempotency_key:string,section_id?:string}` → Job. Requires approved outline. Omit section_id for initial whole course. Include section_id to regenerate only that section. Duplicate idempotency keys return the original Job. Concurrent jobs for the same course are rejected. Provider calls run in a background job; poll below.
- `GET /jobs/{id}` → Job.
- `POST /jobs/{id}/cancel` → Job (an in-flight call can still incur charges).
- `POST /jobs/{id}/resume` → Job. Safe only when no request has been dispatched; uncertain requests are never automatically repeated.
- `PATCH /courses/{id}/sections/{section_id}` `{title?:string,body?:string,answer?:string,explanation?:string}` → Course; saves previous version; edited content is marked for review.
- `POST /courses/{id}/reorder` `{section_ids:string[]}` → Course. Exact set required.
- `GET /courses/{id}/versions` → `{id:number,created_at:string,reason:string,course:Course}[]`.
- `GET /courses/{id}/export?format=html|answers|json` → downloadable learner HTML, separate answer HTML, or structured JSON without original source passages.
- `GET /usage` → `{budget:object,records:Usage[]}`.

Document: `{id,filename,sha256,format:"pdf"|"txt",created_at,passages:Passage[],warnings:string[],is_sample:boolean,cached?:boolean}`.
Passage: `{id,document_id,text,location:string,page:number|null,paragraph:number,heading:string}`. PDF IDs end in `p0001-b0001`; text IDs end in `t0001`. TXT has null page.
DocumentSummary is Document without passages.

Course: `{id,document_id,title,difficulty,mode,options:{modules,assignments,quizzes,questions_per_quiz},outline:{title,module_title,objectives:string[],distribution:{module:1,assignments:1,quizzes:1,questions:number}[],warnings:string[]},outline_approved:boolean,status:"outline"|"ready"|"generating"|"complete"|"needs_review"|"error",sections:Section[],review_flags:string[],created_at,updated_at,version:number}`.

Section: `{id,kind:"objectives"|"introduction"|"readings"|"notes"|"announcement"|"assignment"|"rubric"|"quiz",title,body,answer:string|null,explanation:string|null,evidence:Evidence[],support_status:"supported"|"needs_review"|"proposal",review_notes:string[],edited:boolean,order:number}`. There is one quiz section per question. UI should hide answer/explanation in learner view, render all text as plain text, and offer Show source for evidence. Structure/schedules/rubrics are labeled proposals in section title/body. Course mode `demo` must be visibly labeled **Offline demo**.
Evidence: `{passage_id,quote}`. Quote is validated as an exact substring of the stored passage.
Job: `{id,course_id,section_id:string|null,status:"queued"|"running"|"complete"|"failed"|"uncertain"|"cancelled"|"interrupted",stage:string,error:string|null,created_at,updated_at,estimated_max_usd:number,cancel_requested:boolean}`.
Usage: `{id,job_id,stage,model,input_tokens,output_tokens,cost_usd,status:"completed"|"uncertain",created_at}`.

The first milestone supports one module, one assignment, one quiz, and 1–5 questions. Outline creation is local and a proposal. Real generation includes a separate support-validation call; model support judgments remain fallible and user review is required. Unknown billing outcomes preserve the maximum reservation and are not retried automatically.
