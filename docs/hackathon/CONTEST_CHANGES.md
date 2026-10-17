# Contest-window change record

This record separates the released application from the Nebius hackathon adaptation. Dates use America/Los_Angeles. It is not a claim of eligibility by itself.

## Baseline

- Existing repository: `https://github.com/agammann/easy-street`.
- Baseline release: **v1.0.0**, commit **cc00965b3a667339584742c429d4b212301791dd**.
- Baseline commit time: **October 15, 2026, 10:42:11 p.m. PDT**.
- First repository commit: `1c4a46b468e39d428c03b9b1ea5e44b557f23128`, October 15, 2026, 7:50:17 p.m. PDT.
- Hackathon adaptation branch: **hackathon/nebius-nemotron-2026**, created October 16, 2026 from the clean baseline.

The project already had local React/TypeScript and FastAPI/SQLite operation; PDF/DOCX/TXT extraction and optional local OCR; one to six modules; configurable assignments/quizzes; OpenAI generation and support review; source evidence; manual editing; targeted regeneration; versions; backups and source recovery; archives; learner/answer/JSON exports; private BYO key setup; local budget accounting; and release installation checks on Windows, Linux, and both Mac architectures. Those features must not be represented as new hackathon-branch work.

The [contest window](https://nebiusglobalaihackathon.devpost.com/rules) began August 26, 2026. The observed repository history therefore falls within it. The codebase still existed before this adaptation request, so both the baseline and subsequent changes are disclosed.

## Adaptation ledger

Update the status and evidence as verification finishes. A prepared implementation is not an approved live test or deployment.

| Date | Area | Branch change | Completion evidence |
| --- | --- | --- | --- |
| October 16, 2026 | Provider | `backend/provider.py`, `models.py`, `service.py`, and provider regressions add backend Nebius generation/review while preserving OpenAI contracts | Mock adapter, usage, evidence, malformed-response and bounded-retry regressions passed; approved live Nebius verification remains pending secure key configuration |
| October 16, 2026 | Judging service | `backend/judging.py`, `judging_app.py`, and `demo_control.py` introduce independent visitor workspaces and shared operator accounting, hosted PDF expansion/work limits, and total request deadlines | Mock isolation, deletion, expiry, cutoff, concurrency, PDF-limit and request-deadline regressions passed; real local container acceptance passed with dummy key and zero allowance; remote deployment awaits its approved live-test/final-check conditions |
| October 16, 2026 | Sample and interface | Explicit `backend/sample/LICENSE.txt`; provider-specific source disclosure, hosted session interface, sample generation, and deletion controls | 49 frontend tests and production build passed. Mock-backed desktop/mobile checks covered source/answer/settings navigation and a normal upload → 3 modules/3 assignments/3 quizzes → all 3 exports, with no observed overflow or console errors. Real deployed Nebius acceptance remains pending. |
| October 16, 2026 | Operations | `deploy/` prepares a nonroot multi-stage image, one-instance Fly proposal, smaller Render alternative, and local Compose rehearsal; `scripts/demo_healthcheck.py` adds a read-only diagnostic | Fly TOML parse/control assertions, Render official JSON Schema, and Compose syntax passed; seven mock HTTP diagnostic cases passed; local Linux container build and zero-funded acceptance passed; remote deployment awaits its approved live-test/final-check conditions |
| October 16, 2026 | Live-test safety | `scripts/live_nebius_check.py` keeps private durable accounting and an exclusive `active.lock` around the approved acceptance run | Successful completion releases the matching lock; failure/interruption retains it for manual ledger/outcome review, preventing an automatic repeat of a possibly billed call. No real test has run. |
| October 16, 2026 | Submission material | Rules review, accurate entry draft, video script, license review, judge instructions | Local drafts under `docs/hackathon/`; publication pending |

Operations validation commands used:

```sh
docker compose -f deploy/compose.judging.yaml config --no-interpolate --quiet
python -m py_compile scripts/demo_healthcheck.py
git diff --check
docker build --progress=plain --tag easy-street-judging:qa -f deploy/Dockerfile .
```

The Render Blueprint was parsed with PyYAML 6.0.3 and checked using jsonschema 4.25.1 against the live [official Render JSON Schema](https://render.com/schema/render.yaml.json). Those validation tools were installed into a separate scratch directory, not the application dependency graph. The diagnostic's seven local HTTP cases covered healthy generation, cutoff/readiness separation, protected attention status, malformed JSON, credential redaction, redirect rejection, and origin validation. No real inference or alert was sent by those checks.

Docker Desktop's existing local engine was started through its CLI without accepting an agreement or provisioning a service. A local image built successfully. An acceptance harness then ran it on localhost port 8003 with a dummy key, test access credentials, and **$0 inference allowance**. It verified UID 10001, writable persistent storage, built interface, no development environment file or Node executable in the runtime, login/unauthenticated rejection, source upload, two-session isolation, cutoff before any provider call, three explicit offline exports, restart persistence, deletion, and no fixture credentials in runtime logs. The fixture container, volume, and private environment file were removed afterward. This is real container execution with deterministic offline content and zero live inference; it is not a deployed judging service or a successful Nebius generation test.

The latest rebuilt and acceptance-tested image is **`sha256:6245c4606b06a5d66c20697350139a2cc1fbd5d224cdea1231daa80e1b18528e`**. The refreshed local acceptance record includes a **512 MiB memory / 0.5 CPU** constraint and confirms zero provider calls and $0 measured spending for that fixture run. This constrained offline acceptance does not prove actual remote inference latency, the intended Fly mount's permissions, or every supported upload's peak memory. Any subsequent runtime source changes require rebuilding the affected layers and repeating appropriate acceptance before deployment. The latest complete backend/integration run passed **219 tests with two skips**, including cancellation, whole-request upload deadlines, hosted PDF resource guards, and live-run lock regressions. The frontend passed **49 tests** and its production build. See [VERIFICATION.md](VERIFICATION.md) for commands, distinctions between mocks and real container execution, and remaining live/deployment gates.

A separate constrained profile passed sample PDF/DOCX/TXT uploads, a three-module/30-section offline course, and 100 isolated visitor applications. Peak memory was **100.262 MiB**; memory with 100 visitor applications was **93.078 MiB**, with no OOM event or kill. The first visitor used normal login, and the remaining fixture sessions were seeded inside the disposable container so production login throttles stayed intact. This supports a smaller host candidate for small chapters, while real-host acceptance remains pending. The checked-in Render alternative now uses `0.5c-512mb`; the rejected 2 GB budget is historical only.

## Evidence to retain before submission

Run these from the repository root to identify the actual change set:

```sh
git status --short
git diff --stat cc00965b3a667339584742c429d4b212301791dd
git log --format='%H %aI %s' cc00965b3a667339584742c429d4b212301791dd..HEAD
```

Retain the final source revision, commands and test results, fresh-session screenshots without secrets, provider model and token/cost measurement, deployed image/revision, and verified demo/video URLs. Keep private credentials and original visitor material outside the record. Record any post-deadline operational changes separately; they must not silently replace the submitted functionality.

## Current release gates

The owner approved up to **$1 total for a small Nebius live test** and opening the masked local key prompt on October 16. Credentials are not configured, so the real test and measured cost remain pending. After declining the $85 proposal, the owner approved **Fly hosting and $15 total through December 15**: $8 hosting, $3 aggregate inference including actual development charges, and $4 contingency. Deployment is approved **conditional on final checks and a passing live Nebius test**; the runtime allowance remains zero until then. Credentials, new account agreements, and payment setup stay under the owner's private control. Free Better Stack email monitoring and labeled incident/recovery test alerts to the verified account email are approved, using the read-only operator status endpoint, but no monitor is configured and delivery has not been tested.

A local Devpost entry draft and testing instructions were prepared for review. No Devpost entry was modified or submitted. Preparing these files does not establish a completed entry.

Any spending beyond the approved $15, paid or otherwise unapproved monitoring, public source/video changes, new agreement acceptance, and final entry submission require separate approval. Approved conditional deployment must first satisfy its live-test/final-check gates, and free monitoring must be configured and delivery-tested. No actual deployment, new agreement acceptance, paid provisioning, public hackathon publication, or submission is established by this document.
