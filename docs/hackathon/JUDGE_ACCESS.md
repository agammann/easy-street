# Judging access and acceptance

The approved application is running at **[https://easy-street-agammann-2026.fly.dev](https://easy-street-agammann-2026.fly.dev)** from runtime source **`0c010c00c160e1cb47c60eea7f758050c23a3831`**, including the retention wording and Fly configuration corrections. This public file contains no credentials. The private application code still needs to be added to Devpost's private testing field; no entry has been submitted. Judges need no provider account, payment, or personal API key.

Hosted generation, exports, restart persistence, cached reuse, and editor saves were exercised on the first funded runtime `0e0c17d`. The replacement passed fresh hosted privacy-notice, persistence, ledger, and mobile checks, preserving the provider backend without a new inference call. The raw hosted result is marked `needs_review`, and the edited second copy retains review/dependency flags. Owner content review is pending. See [VERIFICATION.md](VERIFICATION.md) for measured results, current CI and deployment checks, and limitations.

## Private access and intended working period

Judges use the HTTPS URL above and the application-access code supplied privately. It is separate from the operator token and Nebius API key. The host keeps a PBKDF2 access hash and the operator-funded provider key in its secret environment. Do not put any of these values in public documentation; provider/operator keys must never be judge credentials.

Each authenticated browser receives an opaque Secure/HttpOnly/SameSite=Strict cookie and isolated temporary originals, courses, jobs, results, database, and cache. Two hosted HTTP sessions using the same access code were verified to remain independent. A shared access code does not share another visitor's material.

The required availability period runs through **December 15, 2026, noon PST**; configured deployment expiry is the end of December 15 (`2026-12-16T08:00:00+00:00`). The [rules](https://nebiusglobalaihackathon.devpost.com/rules) permit private sites when credentials are supplied and require free judging access. The owner approved a $15 total operating budget through that period. Funding, capacity, expiry, and alerts need continued operator attention; neither this approval nor a passing test guarantees future uptime or imposes a platform billing cap.

Operator setup remains documented in [scripts/configure_judging.py](../../scripts/configure_judging.py). Its hidden prompts create a hash/token in ignored local configuration, start with a zero allowance, and do not request a provider key. The active service now uses approved host secrets and a bounded funded allowance; see [costs and operations](COSTS_AND_OPERATIONS.md). Do not replace secrets or increase allowances as a routine judge workaround.

## Judge testing steps

1. Open **[Easy Street](https://easy-street-agammann-2026.fly.dev)** in a fresh browser window and enter the privately supplied application code. No registration or provider key is required.
2. Choose **Generate sample with Nebius**. Its disclosure identifies the original licensed garden chapter and operator-funded provider. It uses preset one-module/one-assignment/one-quiz settings with three questions, skipping the manual outline steps below. The observed uncached hosted job took **15.8418 seconds** from persisted creation to completion; this is one sample, not a guaranteed wait. Cache hits reuse saved content and must be identified as cached.
3. For a configurable workflow, choose **Try the sample chapter** or upload a PDF, DOCX, or TXT chapter you may process. Hosted uploads are bounded to 5 MiB, three modules, three assignments, and three quizzes. Readable text is required; the judging image does not include optional OCR tools. Review extraction and source coverage, choose counts, and approve the provider disclosure before generation.
4. The selected model is **`nvidia/nemotron-3-super-120b-a12b`** through Nebius Token Factory. Open source evidence, compare the exact quotation and location with the attached claim, and inspect review warnings. The raw sample has an introduction warning and additional support limitations; a completed job does not establish perfect source grounding.
5. Try the editor and version history. Seven corrections were saved in a second cached copy while preserving the raw first result; flags remain for owner review. Export learner HTML, separate answers, and JSON backup. JSON includes answers and selected quotations, so it is not a learner-only handout. A regeneration makes a new bounded provider request; ordinary edits do not.
6. Download anything you want to keep, then use **Delete my workspace**. Two hosted fixture sessions passed deletion acknowledgments and subsequent cookie/resource rejection. Active retention is 24 hours; active work can delay physical cleanup. Normal maintenance removed an owned deliberately expired hosted fixture after 67.94 seconds of observation, without affecting another visitor or accounting; this did not wait a real 24 hours. The Fly volume reports five-day snapshot retention, so existing backup copies may outlive application deletion. Snapshot scheduling/existence is not established by that setting.
7. If access, capacity, or generation fails, use the privately supplied owner contact. The emergency cutoff pauses generation and needs operator intervention. Do not ask judges to fund the account, supply a provider key, or solve a billing problem.

## Private entry fields still needing completion

| Field | Current state |
| --- | --- |
| Application URL and deployed source | [Live HTTPS app](https://easy-street-agammann-2026.fly.dev), runtime `0c010c0`; [CI run 38999513875](https://github.com/agammann/easy-street/actions/runs/38999513875) passed all three runners; image and revision-specific hosted evidence in [verification](VERIFICATION.md) |
| Judge access code | Configured privately; still needs placement in Devpost's private testing instructions |
| Access-help contact | Confirm the owner route before submission; no personal address is published here |
| Observed uncached wait | 15.8418-second hosted job lifecycle; no hosted average/maximum benchmark |
| Cache behavior | Second course completed with identical pre-edit sections and zero new provider calls/cost |
| Restart behavior | Cookie/source/course survived; post-restart hashes matched the pre-restart export |
| Notifications | Availability and protected attention monitors are Up; the owner confirmed both incident-started and resolved emails through the normal free email route |
| Content review | Raw findings preserved; edited second copy still requires owner review |

## Acceptance status and remaining checks

- [x] Fresh unauthenticated hosted requests cannot read protected resources or start generation.
- [x] Login and the real one-click Nebius sample work without BYO credentials; three export downloads were checked for secrets.
- [x] Separate hosted HTTP sessions cannot retrieve each other's documents, course state, jobs, versions, or exports.
- [x] Repeated equivalent work after restart reused saved generation/review with no additional inference.
- [x] Actual 390-pixel browser course and evidence drawer were readable without document overflow or console errors; this is not physical-device testing.
- [x] Hosted fixture deletion invalidated cookies/resources while shared accounting remained intact.
- [x] Source/course content and the authenticated browser session survived an operator-controlled restart.
- [x] Mock/configuration tests cover malformed output, missing credentials, quota/cutoff, cancellation, and failure recovery; hosted zero-budget cutoff was separately exercised.
- [x] An owned deliberately expired hosted fixture was rejected and removed by normal maintenance after 67.94 seconds of observation; no real 24-hour wait was performed.
- [x] The owner confirmed receiving both incident and recovery notifications; no paid upgrade or external outgoing-email integration was used.
- [ ] Complete owner content review, private judge instructions/contact, video approval, and final submission checks.

The working service, source, and recording are complementary evidence. Keep capacity and funded headroom available through judging; an emergency interruption needs a named operator response.
