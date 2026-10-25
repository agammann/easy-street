# Easy Street API contract

Ordinary course routes have base `/api`. JSON responses except uploads and exports. Errors are `{detail: string}`. The default `backend.app:app` entry point is local only: allowed frontend origins are localhost/127.0.0.1 on ports 8000 and 5173. The separate `backend.judging_app:app` gateway authenticates and isolates hosted visitors; see its contracts below. Both serve the built `frontend/dist`. IDs are strings. Source text is untrusted data and must always render as text. Never include provider keys or raw SDK errors in a response.

## Setup and documents

- `GET /health` → `{status:"ok"}`.
- `GET /config` → `{provider,model,key_configured,pricing,budget,providers:ProviderConfig[],hosting_mode:"local"|"judging",demo:null|DemoInfo,privacy_notice,limits,ocr,milestone}`. Local `provider` defaults to `openai`; non-secret `EASY_STREET_PROVIDER=nebius` changes the initial UI choice without changing existing courses or the API's default `CourseInput.mode`. `providers` lists OpenAI and Nebius locally, and only Nebius behind the judging gateway. `limits` retains local ceilings `{modules:6,assignments:6,quizzes:6,max_questions:5,assignments_per_module:2,quizzes_per_module:2,source_chars_per_module:24000}`; in hosted mode use the lower `demo` limits described below. `ocr` is `{available,reason,max_pages:5,language:"eng"}`. The legacy `milestone` limits remain available. No secret is returned; `key_configured` indicates presence, not authenticated model access or actual account balance.
- `GET /session` locally → `{mode:"local",authenticated:true}`. There is no local login; this response does not make the normal entry point safe for public hosting.
- `POST /documents` multipart `file` (PDF, DOCX, UTF-8 TXT; 15 MiB maximum) and optional `ocr_pages` (a JSON array of one to five distinct page numbers) → Document. OCR is local, English, explicit and PDF-only. OCR variants have distinct IDs while retaining the original file digest. Repeat extraction with the same options and output reuses the same document.
- `POST /documents/sample` → the original sample Document, eligible for Offline demo.
- `GET /documents/{id}` → Document; `GET /documents` → summaries without passage text.

Document: `{id,filename,sha256,format:"pdf"|"docx"|"txt",created_at,passages:Passage[],warnings:string[],is_sample:boolean,page_count?:number|null,ocr_pages:number[],needs_ocr_pages:number[],insufficient_text:boolean,cached?:boolean,source_missing?:boolean}`.

ProviderConfig: `{name:"openai"|"nebius",model,pricing:{input_per_million,cached_input_per_million,output_per_million,updated},key_configured:boolean}`. DemoInfo: `{retention_hours,max_upload_mib,max_modules,max_assignments,max_quizzes}`. `GET /sample-license.txt` outside the `/api` base returns the original sample's license notice.

Passage: `{id,document_id,text,location,page:number|null,paragraph:number,heading,ocr?:boolean}`. PDF locations use actual page numbers. TXT/DOCX locations use paragraph numbers, never inferred pages. Sources are bounded to 100 PDF pages and 250,000 extracted characters; course creation requires at least 150 readable characters. A scanned PDF can return a preview with no passages and `insufficient_text:true`; it cannot create a course until enough text is extracted. Imported backups can create a missing-source Document with `source_references` containing locations but no source text.

## Course planning

- `POST /courses` accepts `{document_id,title,difficulty:"introductory"|"intermediate"|"advanced",modules:1..6,assignments:0..6,quizzes:0..6,questions_per_quiz:1..5,mode:"demo"|"openai"|"nebius"}` → Course. Missing `mode` defaults to `openai` in the local API; the judging gateway inserts `nebius` and rejects `openai`. Assignment and quiz totals are course-wide, each at most twice the number of modules. The source needs at least as many passages as modules. Planning is deterministic and free. Offline demo accepts only the included original sample.
- `GET /courses` → Course[], including archived courses. `GET /courses/{id}` → Course.
- `PATCH /courses/{id}/outline` accepts `{title?,modules?:OutlineModule[],module_title?,objectives?}` → Course, saves the previous version and revokes approval. The legacy `module_title` and `objectives` fields update the first module. A modules update supplies the entire array in its original order. Counts must add up to the course options. Each module needs distinct IDs from its source document, at most 24,000 characters. After any generation, its source selections and assessment distribution are fixed; title/objective edits remain allowed and mark saved content for review.
- `POST /courses/{id}/approve` accepts `{provider_disclosure_accepted:true}` → Course.

OutlineModule: `{id:"module-1".."module-6",title,objectives:string[],selected_passage_ids:string[],assignments:0..2,quizzes:0..2}`.

The planner partitions the entire document in source order, including later passages. If a partition exceeds 24,000 characters or 512 actual evidence excerpts, it selects passages throughout that span and explicitly warns about omitted coverage. The outline records the exact selection for review. Each module may have at most two assignments, two rubrics and ten quiz questions, plus five learning sections (19 sections total). The proposed syllabus and course objectives derive from the approved module plan, without another provider call.

Course includes `{id,document_id,title,difficulty,mode,provider?:{name,model},options,outline,outline_approved,status,sections,review_flags,created_at,updated_at,version,generated_module_ids?:string[],archived?:boolean,source_missing?:boolean}`. Status is `outline|ready|generating|complete|needs_review|error`. Outline contains `title,modules,course_objectives,distribution,warnings,selected_passage_ids` and the first-module compatibility fields `module_title,objectives`. Older/imported courses may omit `provider`; `mode` remains the provider-selection authority. No fallback to a different live provider occurs.

## Generation and recovery

- `GET /courses/{id}/estimate?section_id=...` → `{estimated_max_usd,input_tokens_estimate,output_tokens_limit,verification_included:true,provider,model,pricing,budget,notice,provider_calls_max,modules:[{module_id,cached,...}]}`. Estimates sum only unfinished modules or the targeted section, using that provider's pricing. Cached results and Offline demo cost zero; cached generation needs no configured key. Hosted `budget` is the visitor's allowance; dispatch also checks the separate operator ledger.
- `POST /courses/{id}/generate` accepts `{idempotency_key,section_id?:string}` → Job. Requires approval. Without a section ID it generates unfinished modules in order, saving each complete module before proceeding. After cancellation or a safe failure, a new approved request can finish the remaining modules without replacing saved ones. Once all modules exist, regenerate one section at a time. Duplicate request IDs return the original Job; concurrent jobs are rejected.
- `GET /courses/{id}/job` → latest public Job or `null`. Recover progress from this endpoint on reload.
- `GET /jobs/{id}` → Job.
- `POST /jobs/{id}/cancel` → Job. Cancellation is sticky and checked before each provider dispatch. An in-flight call may still incur a charge. Completed modules remain saved.
- `POST /jobs/{id}/resume` → Job. Only interrupted jobs without an in-flight or uncertain request can resume. Persisted generation/verification results and completed modules are reused. No automatic paid retries occur.

Job: `{id,course_id,section_id:string|null,status:"queued"|"running"|"complete"|"failed"|"uncertain"|"cancelled"|"interrupted",stage,error:string|null,created_at,updated_at,estimated_max_usd,cancel_requested,module_ids:string[],total_modules,completed_modules,current_module_id}`. Module counts refer to this request's `module_ids`, not the entire course. Stage is `queued|preparing|generation_in_flight|generation_received|verification_in_flight|verification_received|module_complete|complete|cancelled`. Public jobs omit saved provider outputs and internal module checkpoints.

Each uncached module makes one generation and one separate evidence-review request through its chosen provider. Targeted regeneration uses source passages from that section's module; its review sees the module's complete approved source selection. Cache identity distinguishes providers/models/modes and retains existing OpenAI cache compatibility. There is no cross-visitor cache in hosted mode. Billing uncertainty leaves the remaining maximum reserved and prevents automatic replay. A malformed or refused response with known token usage remains charge-accounted; unknown billable outcomes are not treated as free. Budget is cumulative per local database across both providers, not per course, provider, or day.

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

## Provider boundary

OpenAI uses its Responses API and pinned model `gpt-4.1-mini`. Nebius uses `https://api.tokenfactory.nebius.com/v1/chat/completions` and pinned model `nvidia/nemotron-3-super-120b-a12b`, with a strict JSON schema, reasoning disabled, and bounded completion tokens. Both adapters use the existing SDK with `max_retries=0`, 90-second timeout, and `store=False`. Generation is bounded to 8,000 output tokens per module and support review to 3,500. These options do not establish a provider retention contract or authenticated availability.

Generation selects catalog evidence IDs that the application expands into exact source quotations, then validates structure and support. There are no web search, retrieval, code-execution, or arbitrary URL tools. Source/outline/generated text is untrusted; prompt defenses and automated entailment review are fallible. Missing or conflicting support must remain visible for human review.

## Separate judging gateway

These routes exist only in `backend.judging_app:app`; the ordinary API routes above remain scoped to the authenticated visitor's child application.

| Route | Contract |
| --- | --- |
| `GET /health/live` | Public `{status:"ok",generation_available:boolean}`; process liveness, no inference call. |
| `GET /health/ready` | Public 200 when a provider key is configured; 503 with `status:"not_ready"` when absent. `generation_available` also checks positive shared allowance and deployment expiry. A 200 does not prove valid credentials, reachable provider/model, sufficient balance for a particular request, or a working full workflow. |
| `GET /api/session` | `{mode:"judging",authenticated,retention_hours,expires_at:string|null,csrf_token?:string}`. The CSRF token is returned only for a current session. |
| `POST /api/session` | JSON `{access_code:string}` → session response and opaque `easy_street_judging` cookie. Invalid code 401, rate-limited 429, session capacity 503. Code is checked against the configured PBKDF2 hash. Cookie is HttpOnly, SameSite=Strict, Secure for HTTPS, with bounded lifetime. |
| `DELETE /api/session` | Requires session cookie and `X-Easy-Street-CSRF`. Returns `{deleted:true}`, removes visitor files/state and cookie. Active work can return 409; finish/cancel and retry. Non-content operator accounting survives deletion. |
| `POST /api/sample-course` | Requires session/CSRF and `{provider_disclosure_accepted:true,idempotency_key:string}`. Returns `{course,document,job}` for one original-sample Nebius module, one assignment and one quiz of three questions, reduced if the operator configured zero assessments. Starts the normal real-provider background path; zero funding blocks dispatch rather than substituting Offline demo. Duplicate session/request IDs return the same saved result. |
| `GET /api/operator/status` | Separate bearer operator token; never a judge/provider key. Returns `budget:{limit_usd,spent_usd,reserved_usd,remaining_usd,uncertain_calls}`, configuration/expiry/cleanup flags, `needs_attention`, and `provider_balance_verified:false`. No source content, answers, credentials, or actual provider credit balance. |

Mutating authenticated requests require the exact CSRF header; Host and Origin must match the configured origin. Unauthenticated private API requests return 401. The public health routes permit internal localhost probes and expose no visitor data. Request-body reading has a total sixty-second deadline, reduced to ten seconds for login; exceeding it returns 408 and closes the connection. Hosted `/api/courses/import` is disabled (422); backups can be imported in a local installation. Exports, source reattachment, editing, and normal upload/course routes remain visitor-scoped.

Prepared hosted defaults: 5 MiB uploads; at most 100,000 extracted characters/1,000 passages/2 MiB document JSON; five sources and twelve courses per visitor; three modules, three assignments and three quizzes; 24-hour retention; 100 sessions; 120 requests/minute per session; eight login attempts/minute per client and sixty globally. The global request gate admits at most sixteen active API requests; a two-call semaphore bounds concurrent provider dispatch with a twenty-second wait. Admission checks also reserve storage headroom under a 32 MiB visitor and 700 MiB shared workspace ceiling. The single mounted data directory uses one application process.

Hosted PDF extraction applies context-local pypdf bounds: 8 MiB per declared/decoded stream or image buffer, 32 MiB decoding work per stream, and 1,000 page-tree entries. An upload within the original byte limit can still be rejected for expansion/work. These limits apply only to the judging visitor service and reset when extraction finishes or fails; normal local extraction settings remain unchanged.

Cleanup runs at startup and approximately every sixty seconds, removing expired/orphan visitor directories when no active request/worker is using them. Active work can delay physical deletion; expiration already blocks further visitor access. Provider calls retain independent shared accounting/reservations. A process restart marks global in-flight calls uncertain instead of releasing their maximum. Default operator allowance is zero; reaching the cutoff interrupts judging and needs intervention. `needs_attention` includes the final 20% (minimum $0.10), uncertain calls, missing key, cleanup failure, and deployment or verified credit expiry within seven days.

The local entry point is `backend.app:app`; it loads local environment configuration. The hosted `backend.judging_app:app` deliberately does not load `.env` or `.env.local`. Import `backend.main.create_app` for isolated tests; importing the factory alone does not load environment files or open a default database. Run one server process per data directory so restart recovery and concurrency control belong to that instance. See [architecture](../docs/hackathon/ARCHITECTURE.md) and [operations](../docs/hackathon/COSTS_AND_OPERATIONS.md) for deployment gates and limits.
