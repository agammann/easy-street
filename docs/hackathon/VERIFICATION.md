# Hackathon branch verification

Checked October 16, 2026 on `hackathon/nebius-nemotron-2026`, extending released baseline `cc00965b3a667339584742c429d4b212301791dd`. The initial tree was clean. Local preparation and two real Nebius sample runs are verified below. A publicly deployed judging service and delivered monitoring alerts are not yet established.

## Automated and container results

| Check | Result | Scope |
| --- | --- | --- |
| `python -m pytest backend/tests tests/integration -q` | **276 passed, 3 skipped**, 35.58 seconds | Both provider contracts; source support/missing/conflicting evidence; malformed output; retry limits; cache/duplicates and prompt-version invalidation; reservations, billing uncertainty, and cutoff; secrecy; visitor isolation; deletion/TTL; admission/concurrency; cancellation and body deadlines; setup safety and exclusive live-test lock; hosted PDF expansion limits; release/archive safety; durable provider failure/recovery flags |
| `pnpm -C frontend test` | **49 passed** | Existing editing/planning plus provider disclosures, session gate, sample idempotency, retention/deletion, hosted controls and loading privacy |
| `pnpm -C frontend build` | **Passed** | TypeScript and production assets |
| `git diff --check` | **Passed** | No whitespace errors; Windows line-ending normalization warnings are informational |
| Render Blueprint validation | **Passed** | Official JSON Schema, plus Compose syntax; no service created |
| `fly config validate --config deploy/fly.toml --strict` | **Passed** | Authenticated Fly CLI validation; no resource provisioned |
| Health diagnostic | **7 mocked cases passed** | GET-only health/attention checks, redaction, malformed/redirect failures; no monitor installed |
| Container build and runtime acceptance | **Passed** | Real local Linux container; dummy credentials, explicit offline content, zero inference allowance |
| Packaging and Python-only ZIP installation | **Passed locally** | 117 public files; exact reviewed environment-template paths; executable LF macOS launcher; fresh Python environment inside a disposable Linux container without Node; launcher, complete offline workflow, exports, restart, and zero provider usage |

The backend skips are optional real OCR without Tesseract and two Windows symlink fixtures without permission. One existing Starlette/httpx deprecation warning remains. Routine provider tests use mocked transports/providers; they do not establish remote model availability or generation quality. The implementation is published in [draft PR #1](https://github.com/agammann/easy-street/pull/1). Check [the PR checks](https://github.com/agammann/easy-street/pull/1/checks) for the intended revision before a release or deployment.

The first independent [CI run on `6524760`](https://github.com/agammann/easy-street/actions/runs/38995392375) passed backend/integration tests (221 on Linux; 220 passed and one skipped on each Mac), 49 frontend tests, the build, and production/offline smoke on Linux, Apple Silicon macOS, and Intel macOS. All three then failed packaging because the public `deploy/.env.judging.example` template was rejected. The follow-up permits only that exact template and the existing root `.env.example`, retaining rejection of private environment files, runtime data, database sidecars, logs, and links. Regression tests also verify canonical staged source bytes and removal of inherited keys for both providers during smoke tests.

[CI run `38995934439`](https://github.com/agammann/easy-street/actions/runs/38995934439) is fully green at `1f75aa907e647b06bb416b4ae13536281842aaf9`: Linux 268 backend/integration tests passed; both Macs 267 passed and one skipped; frontend 49 passed on every runner. All three passed the production smoke, packaging, fresh Python-only ZIP installation, launcher startup/shutdown, and complete offline workflow. Their 117-file archives had identical SHA-256 `eb5483b95a64c677682f657e2ce04a6f29060560f736980cf9bc7581a792d322`. Later provider-health/prompt changes have separate local results above and must be checked at their intended revision.

The final local image was built with:

```sh
docker build --progress=plain --tag easy-street-judging:qa -f deploy/Dockerfile .
```

Acceptance-tested prompt 2.1 image: **`sha256:c5766ffd14db8851a766bed0e72aca273ec6f01a0cdadc560cb780217ae50997`**. The harness verified UID 10001, writable persistent storage, built frontend, absence of developer `.env.local` and Node in runtime, login/rejection, upload, two independent visitor sessions, inaccessible cross-session resources, zero-budget rejection before dispatch, three offline exports, restart persistence, deletion, and fixture credentials absent from logs/exports. Temporary container, volume, and test environment file were removed. This test made **0 provider calls and incurred $0 API cost**.

The final acceptance ran under **512 MiB total memory/swap and 0.5 CPU**. A separate constrained profile on earlier image `6245c460` tested PDF/DOCX/TXT sample uploads and a three-module, 30-section offline course, then instantiated 100 isolated visitor applications through authenticated HTTP. The first session used real login; the other 99 fixture sessions were seeded inside the disposable container to preserve production login throttles. Startup was 2.181 seconds; current memory after 100 visitors was 93.078 MiB; whole-test peak was **100.262 MiB**, including brief fixture helpers. No OOM event or kill occurred. The profile predates the provider-health/prompt changes; final-image acceptance above was repeated afterward. These checks support the cheaper 512 MiB hosting candidate for small chapters, without proving worst-case uploads, actual host performance, or live inference latency.

A separate network-disabled local bootstrap rehearsal simulated an empty, root-owned disk using Docker `volume-nocopy`. UID 10001 could not initially write. An administrative process verified the exact mount, applied nonrecursive ownership 10001:10001 and mode 0700 to that directory only, then verified write/remove as UID 10001 while the application process stayed nonroot. Its disposable resources were removed. This validates the local permission sequence, not an actual Fly volume.

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

## Real Nebius evidence and remaining deployment gates

The owner approved **up to $1 cumulative for live Nebius acceptance**, separate from any earlier OpenAI approval. The development key was created and saved directly into ignored local configuration without printing it, and the one-time key view was closed. Both runs verified `nvidia/nemotron-3-super-120b-a12b` in the authenticated catalog. Only the original licensed chapter was used.

| Real run | Input tokens | Output tokens | Estimated cost from usage | Wall time |
| --- | ---: | ---: | ---: | ---: |
| Initial generation | 2,189 | 1,010 | $0.0015657 | Included below |
| Initial support review | 3,795 | 387 | $0.0014868 | 8.62 seconds total |
| Prompt 2.1 generation and review | 8,079 | 1,878 | $0.0041139 | 10.50 seconds |
| **Cumulative** | **14,063** | **3,275** | **$0.0071664** | Two small local samples |

Both jobs completed ten sections with exact source quotation matches, no outstanding reservations or uncertain calls, and zero automated review flags. These are real provider-reported tokens at the configured rates, not mocked cost figures or a verified invoice. The second test reused the original persistent one-dollar ledger and exclusive lock; hashes confirmed the first run's course/result/state evidence was unchanged. No automatic retries were made.

Separate inspection found that the initial introduction cited only the title and added an absorption guarantee. Prompt 2.1 now requires support from each section's own cited quotations, preserves approximations, and invalidates prior cached generation/review for both providers. Its sample removed that guarantee and added substantive citations, but inspection still found incomplete citation coverage and precision issues. Zero automated flags therefore does **not** establish perfect factual support. Owner content review and deliberate corrections remain necessary; raw results are retained without rewriting the evidence.

A no-inference guard test reused a private copy of the first real result: duplicate submission returned the same job, a new equivalent course hit generation/review cache, all ten sections matched, and usage/ledger/evidence hashes stayed unchanged with zero provider attempts. This verifies reuse of actual live output, not another live generation. Private evidence is kept outside the public repository.

The owner approved and confirmed **Fly.io with a $15 total cap through December 15**, with deployment conditional on final checks and passing live acceptance. Fly CLI sign-in and strict configuration validation are complete; no paid hosting resources are provisioned. Free Better Stack email monitoring, its account terms/privacy, and labeled incident/recovery test alerts are approved. Signup reached email verification; monitor configuration and delivery remain untested. There is currently **no public judging demo or configured monitor**. Promotional expiry remains unverified; the paid inference fallback is bounded by the approved aggregate $3 less actual development usage. After deployment, repeat the whole workflow in a fresh browser session and verify alert receipt; local success does not substitute for those checks.

See [eligibility](ELIGIBILITY.md), [costs and operations](COSTS_AND_OPERATIONS.md), [judge access](JUDGE_ACCESS.md), [change record](CONTEST_CHANGES.md), and [the video script](VIDEO_SCRIPT.md). The branch and draft PR were published with approval. Merging or making a new release, video publication, new agreements and final submission remain separate owner approvals.
