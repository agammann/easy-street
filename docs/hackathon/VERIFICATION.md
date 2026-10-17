# Hackathon branch verification

Checked October 16, 2026 on `hackathon/nebius-nemotron-2026`, extending released baseline `cc00965b3a667339584742c429d4b212301791dd`. The initial tree was clean. This report covers local preparation; it does not establish a publicly deployed service or a successful real Nebius call.

## Automated and container results

| Check | Result | Scope |
| --- | --- | --- |
| `python -m pytest backend/tests tests/integration -q` | **265 passed, 3 skipped**, 34.52 seconds | Both provider contracts; source support/missing/conflicting evidence; malformed output; retry limits; cache/duplicates; reservations, billing uncertainty, and cutoff; secrecy; visitor isolation; deletion/TTL; admission/concurrency; cancellation and body deadlines; setup safety and exclusive live-test lock; hosted PDF expansion limits; release/archive safety and smoke-environment isolation |
| `pnpm -C frontend test` | **49 passed** | Existing editing/planning plus provider disclosures, session gate, sample idempotency, retention/deletion, hosted controls and loading privacy |
| `pnpm -C frontend build` | **Passed** | TypeScript and production assets |
| `git diff --check` | **Passed** | No whitespace errors; Windows line-ending normalization warnings are informational |
| Render Blueprint validation | **Passed** | Official JSON Schema, plus Compose syntax; no service created |
| Health diagnostic | **7 mocked cases passed** | GET-only health/attention checks, redaction, malformed/redirect failures; no monitor installed |
| Container build and runtime acceptance | **Passed** | Real local Linux container; dummy credentials, explicit offline content, zero inference allowance |
| Packaging and Python-only ZIP installation | **Passed locally** | 117 public files; exact reviewed environment-template paths; executable LF macOS launcher; fresh Python environment inside a disposable Linux container without Node; launcher, complete offline workflow, exports, restart, and zero provider usage |

The backend skips are optional real OCR without Tesseract and two Windows symlink fixtures without permission. One existing Starlette/httpx deprecation warning remains. Routine provider tests use mocked transports/providers; they do not establish remote model availability or generation quality. The implementation is published in [draft PR #1](https://github.com/agammann/easy-street/pull/1). Check [the PR checks](https://github.com/agammann/easy-street/pull/1/checks) for the intended revision before a release or deployment.

The first independent [CI run on `6524760`](https://github.com/agammann/easy-street/actions/runs/38995392375) passed backend/integration tests (221 on Linux; 220 passed and one skipped on each Mac), 49 frontend tests, the build, and production/offline smoke on Linux, Apple Silicon macOS, and Intel macOS. All three then failed packaging because the public `deploy/.env.judging.example` template was rejected. The follow-up permits only that exact template and the existing root `.env.example`, retaining rejection of private environment files, runtime data, database sidecars, logs, and links. Regression tests also verify canonical staged source bytes and removal of inherited keys for both providers during smoke tests. Packaging and complete ZIP-install checks must pass on the corrected revision before release.

The final local image was built with:

```sh
docker build --progress=plain --tag easy-street-judging:qa -f deploy/Dockerfile .
```

Acceptance-tested image: **`sha256:6245c4606b06a5d66c20697350139a2cc1fbd5d224cdea1231daa80e1b18528e`**. The harness verified UID 10001, writable persistent storage, built frontend, absence of developer `.env.local` and Node in runtime, login/rejection, upload, two independent visitor sessions, inaccessible cross-session resources, zero-budget rejection before dispatch, three offline exports, restart persistence, deletion, and fixture credentials absent from logs/exports. Temporary container, volume, and test environment file were removed. This test made **0 provider calls and incurred $0 API cost**.

The final acceptance ran under **512 MiB total memory/swap and 0.5 CPU**. A separate constrained profile tested PDF/DOCX/TXT sample uploads and a three-module, 30-section offline course, then instantiated 100 isolated visitor applications through authenticated HTTP. The first session used real login; the other 99 fixture sessions were seeded inside the disposable container to preserve production login throttles. Startup was 2.181 seconds; current memory after 100 visitors was 93.078 MiB; whole-test peak was **100.262 MiB**, including brief fixture helpers. No OOM event or kill occurred. This supports the cheaper 512 MiB hosting candidate for small chapters; it does not prove worst-case 5 MiB uploads, actual host performance, or live inference latency.

Hosted PDF parsing now limits declared/decoded/image streams to 8 MiB, decoding work to 32 MiB per stream, and page-tree entries to 1,000. A compressed PDF fixture below 1 MiB with a 9 MiB expanded stream is rejected. Context-local configuration resets after failure and leaves regular local extraction limits unchanged. These bounds reduce expansion risk; they are not a proof that every adversarial document is harmless.

## Browser and visual checks

The built interface ran against a clearly labeled mocked Nebius backend on localhost. Browser automation used the available in-app browser; the separate Browser plugin was unavailable. Desktop and 390-pixel mobile layouts were inspected.

- Private login, temporary-storage disclosure, one-click original sample, completed course, exact source drawer, learner/answer-key separation, and provider/usage settings worked.
- Normal upload of the licensed TXT chapter, extraction review, configurable three-module/three-assignment/three-quiz outline, approval, estimate, and generation completed. Learner HTML, separate answers, and JSON downloads all succeeded.
- No document-level horizontal overflow was observed in mobile course/settings views; no browser warning/error logs were captured during those checks. This is responsive desktop-browser testing, not physical-device testing.
- Delete-workspace confirmation and cancellation worked in the browser. Actual deletion, active-job rejection, expiry/orphan cleanup, and restart persistence were verified by automated/container tests.
- Two discovered UI issues were fixed and retested: hosted backup import was offered despite server rejection, and loading privacy text briefly described local storage. Hosted import is now omitted and loading copy is neutral.
- Backend review found and fixed a cancelled write-lock waiter that could strand future saves, and stalled request bodies that could occupy admission slots indefinitely. Regression tests cover cancellation, timeout, total trickle deadline, safe 408 responses, released slots and visitor pins.

The existing normal local installation also opened successfully with persisted courses and both BYO provider metadata entries. Its existing OpenAI configuration and usage were preserved; no additional OpenAI call was made for this branch verification.

## Live and deployment evidence still required

The owner approved **up to $1 total for live Nebius acceptance**, separate from any earlier OpenAI approval. The masked local setup window was opened with permission. At the last check no Nebius key was configured; no real inference has run, so actual tokens, latency, support quality and measured cost are **not yet available**. The protected persistent live harness must verify the exact model in the account catalog before inference. A mock token estimate must not be reported as measured API cost.

The owner approved and confirmed **Fly.io with a $15 total cap through December 15**, with deployment conditional on final checks and a passing live Nebius test. Free email monitoring and labeled incident/recovery test alerts are approved, but account configuration and delivery remain untested. There is currently **no public judging demo, no configured monitor, and no confirmed promotional-credit expiry or paid fallback**. Runtime source changes after this image require rebuilding and repeating affected acceptance. After approved deployment, repeat the whole workflow in a fresh browser session and verify alert receipt; local container success does not substitute for those checks.

See [eligibility](ELIGIBILITY.md), [costs and operations](COSTS_AND_OPERATIONS.md), [judge access](JUDGE_ACCESS.md), [change record](CONTEST_CHANGES.md), and [the video script](VIDEO_SCRIPT.md). The branch and draft PR were published with approval. Merging or making a new release, video publication, new agreements and final submission remain separate owner approvals.
