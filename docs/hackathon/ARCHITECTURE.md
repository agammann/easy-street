# Easy Street architecture

The hackathon branch extends the released React/TypeScript, FastAPI, and SQLite application. It keeps the local installation and its OpenAI default, adding a Nebius adapter and a separate private judging gateway. It does not replace the original application or require local users to share an operator account.

## Local and hosted entry points

| Component | Normal local installation | Private judging configuration |
| --- | --- | --- |
| Entry | `backend.app:app`, launched by `start.py`/`launch.py` | `backend.judging_app:app` |
| Configuration | Process environment, then `.env.local` and `.env` without overwriting process values | Process/runtime secret environment only; no local env-file loading |
| Provider | Per course: OpenAI, Nebius, or authored Offline demo; OpenAI is the API/default UI choice | Nebius or explicit Offline demo; OpenAI requests rejected |
| Storage | One local `data/` workspace | Dedicated temporary directory, SQLite database and cache for each visitor |
| Billing | User-owned provider keys and a cumulative local allowance | Operator-owned Nebius key, visitor allowance, and shared persisted ledger |
| Access | Loopback plus fixed local Host/Origin protections | Private access code, opaque session cookie, exact Host/Origin, CSRF protection |

`EASY_STREET_PROVIDER` controls the initial local UI choice, not existing courses or the API schema's default. Both providers can be configured at once; unavailable generation never silently changes provider. `GET /api/config` returns presence indicators and model/pricing metadata, never provider keys. A configured indicator does not prove working credentials or funding.

## Source and generation path

```mermaid
flowchart LR
    U[Permitted PDF, DOCX or TXT] --> E[Bounded local/server extraction]
    E --> P[Review passages and deterministic outline]
    P --> A[Explicit source/provider approval]
    A --> J[Persisted job and visitor/local reservation]
    J --> C{Saved cache entry?}
    C -->|yes| R[Reuse generated content and support review]
    C -->|no| B[Provider-specific bounded dispatch]
    B --> G[Strict schema and evidence catalog IDs]
    G --> Q[Expand exact source quotations]
    Q --> V[Separate source-support review]
    V --> S[Persist module and recorded usage]
    R --> S
    S --> H[Human review, edit, evidence view and export]
```

The extractor creates stable source locations: actual PDF pages or TXT/DOCX paragraph references. It does not fetch URLs, execute document commands, or run macros. Local optional OCR explicitly processes selected pages using installed tools. The prepared judging image omits OCR and accepts one readable chapter within smaller limits.

The planner partitions approved source coverage into bounded modules. Long partitions can omit passages; warnings and exact selections are visible before approval. Each uncached module makes one generation request and one support-review request. A section regeneration uses its module's sources and preserves unrelated edits. Successful stages and modules persist for safe recovery. Uncertain in-flight outcomes are never automatically replayed.

`backend/provider.py` contains two adapters using the existing SDK:

- OpenAI: Responses API, `gpt-4.1-mini`.
- Nebius: Token Factory Chat Completions API, `nvidia/nemotron-3-super-120b-a12b`, strict JSON schema, thinking disabled, bounded output.

Both disable SDK retries, use a 90-second request timeout, and request `store=False`. The app validates returned structure and expands only evidence IDs from its supplied catalog into exact quotes. Models cannot choose arbitrary source locations. Missing or conflicting evidence raises review states rather than becoming verified material. Requests have no external search, retrieval, execution, or URL-access tools.

## Hosted request and accounting boundary

```mermaid
sequenceDiagram
    participant B as Judge browser
    participant G as Judging gateway
    participant W as Visitor Service and SQLite
    participant L as Shared operator ledger
    participant N as Nebius Nemotron
    B->>G: HTTPS login with private application code
    G-->>B: Opaque HttpOnly cookie and CSRF token
    B->>G: Approved source/course request with cookie and CSRF
    G->>G: Check origin, session, request/count/storage limits
    G->>W: Route only to this visitor's workspace
    W->>W: Check duplicate ID, cache, approval and visitor reservation
    W->>L: Acquire bounded call slot; atomically reserve maximum
    L->>N: Server-side inference using runtime key
    N-->>L: Output and token usage, or uncertain/rejected outcome
    L->>L: Record actual usage or retain uncertain reservation
    L-->>W: Validated result or safe error
    W-->>B: Course, evidence, progress and non-secret usage
```

The gateway hashes the opaque cookie for session lookup. The cookie is Secure under HTTPS, HttpOnly, SameSite=Strict, and limited by retention/deployment expiry. Each visitor receives its own `visitors/<id>/` database, originals, jobs, versions, and cache. Identical hashes or request IDs in a second session do not grant access to the first. Frontend remembered workspace IDs are cleared when the session ends. Authentication is a private judging convenience, not a general account/role system.

`MeteredProvider` wraps the hosted Nebius adapter. Before each dispatch, `DemoLedger` acquires one of the bounded call slots and uses a SQLite transaction to reserve cost against all visitors' spend plus outstanding reservations. Known token usage is recorded even when output validation fails. Rejected dispatches release their reservation; ambiguous failures and interrupted calls retain it. Visitor deletion cannot reset the shared allowance. No operator provider key is persisted in either database.

The global ledger contains model, stage, pseudonymous session ID, timestamps, token counts, actual estimated cost, and reservation/state. It contains no uploaded source, course answers, or provider key. Local/visitor job records provide their separate course-level allowance and recovery. Cache identity includes the provider/model/mode and prompt/source/settings; OpenAI compatibility is preserved, and no shared visitor-content cache is introduced.

Default hosted controls include 5 MiB uploads, 100,000 source characters/1,000 passages, three modules and three of each assessment, five sources/twelve courses per visitor, 24-hour sessions, a $0.50 visitor allowance, and two concurrent provider calls. Total body-read deadlines are sixty seconds for bounded uploads and ten seconds for login; timed-out requests release their admission slots. Additional request, login, storage, and queue gates are specified in [API_CONTRACT.md](../../backend/API_CONTRACT.md). The global allowance starts at **zero until the approved deployment's final checks and live Nebius test pass**; then only the remaining approved inference amount may be enabled. One instance and one Uvicorn worker own the mounted data directory; scaling the process would bypass in-memory concurrency gates and is unsupported.

Hosted PDF extraction applies context-local pypdf limits: at most 8 MiB per declared/decoded stream or image buffer, 32 MiB decoding work per stream, and 1,000 page-tree entries. These restrict expansion/work beyond the original upload size. They apply only to the judging visitor service, leaving normal local extraction settings unchanged. They are resource guards, not a proof that every malformed document can be processed safely or within a particular latency.

## Retention and operational limits

Workspace deletion removes its originals, database, courses, versions, and cache once active work has stopped, then removes the session cookie. Expired sessions cannot read their data. Startup and minute-scale maintenance remove expired/orphan workspaces when safe; active requests can delay physical cleanup. Non-content global accounting remains for reconciliation. Host snapshots/backups can retain deleted bytes independently and need an approved retention policy before real deployment.

Liveness/readiness checks never invoke a model. Readiness distinguishes absent configuration from positive allowance/deployment expiry, but does not authenticate against Nebius or prove that a particular course fits the budget. The protected operator endpoint reports attention flags and explicitly says actual provider balance is unverified. Free Better Stack email monitoring and labeled test alerts to the verified account email are approved, using the read-only operator status endpoint. They remain unconfigured and delivery is untested. See [costs and operations](COSTS_AND_OPERATIONS.md).

## Trust limits and evidence

Uploaded text, outlines, and prior generated sections are untrusted data. System instructions tell both adapters to ignore embedded role changes, commands, URLs, exfiltration requests, and unsupported factual additions. No key or hosting secret enters a model prompt; tools that could follow such instructions are absent. Escaped text rendering and browser policy restrict executable content.

These measures reduce exposure but do not prove that a model will always ignore malicious text or avoid its pretrained knowledge. A valid exact quote may still fail to entail the attached claim, and an automated reviewer can miss that. User-selected coverage can also omit a conflicting passage. The product therefore preserves uncertainty, shows evidence and review warnings, and requires human review. It does not promise correct teaching across arbitrary subjects or adversarial documents.

Routine adapter, evidence, malformed-response, retry, caching, duplicate, budget, secrecy, and session tests use mocks. The local Linux container acceptance used a dummy key, zero paid allowance, and explicit authored offline content. Live Nebius generation, measured token cost, deployed fresh-session acceptance, and actual alert delivery remain separate approval-dependent evidence. See [the contest change record](CONTEST_CHANGES.md) before making claims about readiness.
