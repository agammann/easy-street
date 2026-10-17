# Easy Street — Devpost draft

Entry draft for review, included on the public hackathon branch. It has not been submitted to Devpost. Replace the remaining verification fields with measured results before using this as the final entry. Two local real Nebius runs and a funded hosted sample passed technical checks, including revised prompt v2.1. The [working Fly deployment](https://easy-street-agammann-2026.fly.dev) is active. Content support still requires owner review; do not portray a completed job as final content acceptance. No Devpost entry was modified or submitted by this preparation.

## Project name

Easy Street

## Elevator pitch

Turn a chapter you own into an editable mini-course, with source evidence beside the lessons, assignments, and quizzes.

## Inspiration

An instructor or independent learner often has good source material but little time to turn it into a useful sequence of lessons and practice. A plausible-looking draft is not enough: readers need to inspect what supports its statements. Easy Street brings the chapter, proposed learning structure, and evidence review into one workspace.

## What it does

Upload a readable PDF, DOCX, or TXT chapter, or start with the included original sample. Review the extraction, choose a bounded number of modules and assessments, and approve an outline. Easy Street drafts learning notes, activities, rubrics, and quizzes from selected source passages. Evidence links show the supporting locations and quotations. A separate support review can flag missing or conflicting evidence; the user can edit the result and regenerate a section without replacing unrelated edits.

Learner HTML, separate answer-key HTML, and JSON backup exports make the work usable beyond the browser. Regular installations run locally with the user's own provider key. The judging configuration is a separate, operator-funded service with private visitor workspaces, explicit deletion, short retention, and server-side spending controls.

## How we built it

We extended the released Easy Street repository rather than starting a new application. React and TypeScript provide the editor; FastAPI and SQLite handle extraction, course state, versions, jobs, evidence, caching, and usage reservations.

The contest integration adds Nebius Token Factory as a backend provider while preserving OpenAI support. Its configured model is **`nvidia/nemotron-3-super-120b-a12b`**. The authenticated catalog and all three approved local/hosted runs verified that identifier, including revised prompt v2.1; see [verification](VERIFICATION.md). Owner content review and any further corrections are still required; seven edits in the second hosted copy are documented below. Token Factory is wired to the actual generation and support-review calls. No web search or external retrieval contributes educational claims. Source passages and outline text are treated as untrusted data, including instructions embedded in a document.

The hosted demo keeps the operator's Nebius key in the server's secret environment. Browsers receive course results and non-secret configuration, never provider credentials. Bounded uploads, module/token limits, duplicate-request handling, concurrency control, and persistent usage accounting constrain operator exposure.

## Challenges

Source quotations are necessary but do not automatically substantiate every sentence that cites them. We kept exact evidence checks separate from semantic support review and made uncertainty visible. We also had to adapt a personal local workspace into isolated temporary visitor workspaces without weakening the original bring-your-own-key installation.

## Accomplishments

- Preserved editable modules, configurable assessments, evidence views, and recovery from the released application.
- Kept provider credentials on the backend and retained source-only course generation.
- Deployed an operator-funded judging service with isolated visitor workspaces and an original sample workflow, preserving normal BYO installations.
- The corrected public revision passed Linux, Apple Silicon Mac, and Intel Mac CI, including tests, build, packaging, production smoke, and fresh Python-only ZIP installation. Local 512 MiB/0.5 CPU container acceptance also passed with explicit offline content. See [verification](VERIFICATION.md) for exact revision-specific counts and the scope of mocks.
- Three real local/hosted jobs total 20,932 input / 5,801 output tokens and $0.0115005 estimated from reported usage. The hosted one-click job completed ten sections and three questions in 15.8418 seconds, with $0.0043341 estimated cost. Exact quotations and completion did not establish complete support: the raw hosted course is `needs_review` and additional claim-strength/citation gaps were found.
- The actual hosted course/source and authenticated session survived restart. A second course reused the persisted generation/review cache with identical pre-edit sections and zero new calls or cost. Seven subsequent edits advanced only that second copy from version 5 to 12; raw first-run evidence was preserved and review/dependency flags remain for owner review.
- Desktop and 390-pixel evidence views, all three exports, two-session HTTP isolation/deletion, and an owned expired-fixture cleanup were tested on the actual service. The expiry test exercised scheduled maintenance without waiting a real 24 hours. Two free monitoring checks are Up; the owner confirmed receiving both incident-started and resolved emails from a labeled test, with no paid upgrade or external outgoing-email integration. See [verification](VERIFICATION.md) for precise limits.

## What we learned

An educational generation tool needs clear source boundaries, recovery, and readable review controls as much as model output. A model can preserve an exact quotation while adding a claim the quotation does not establish. The tool therefore supports human inspection rather than asserting that automated checks guarantee correctness.

## What's next

Evaluate broader subject matter and longer sources using material we may legally process. Improve support-review quality using reproducible cases while preserving uncertainty. Broader classroom workflows, grading, and LMS integration remain future work rather than claims about this build.

## Track and technologies

Best Apps and Agents. React, TypeScript, FastAPI, SQLite, Nebius Token Factory, NVIDIA Nemotron, OpenAI-compatible SDK, PDF/DOCX/TXT extraction, Fly.io, and Better Stack free monitoring. No paid monitoring upgrade or external email integration was configured.

## Nebius and NVIDIA feedback

Observed in the first approved sample: Token Factory accepted the configured Nemotron model and returned schema-valid generation and support-review responses. The complete ten-section job took 8.62 seconds and reported 5,984 input / 1,397 output tokens. Exact quotations were retained. However, the support review returned zero flags while a separate inspection found a title-only factual citation and stronger assurance wording than the chapter supports. Revised prompt v2.1 and a new cache identity completed a second real sample in 10.50 seconds, reporting 8,079 input / 1,878 output tokens. Its introduction cites substantive source material and no longer adds the absorption guarantee. Separate inspection still found citation-coverage and approximation gaps despite zero automatic flags. The third sample ran on Fly: generation used 2,263 input / 1,529 output tokens and support review used 4,606 / 997, totaling $0.0043341 estimated cost and a 15.8418-second job lifecycle. The hosted result retained a review warning, and inspection found further unflagged support gaps. Restart and cached reuse passed without another provider call. These three small samples verify integration and expose review limits; they are not a platform-wide quality or latency benchmark.

## Existing project and contest changes

Easy Street v1.0.0 existed before this hackathon adaptation. Its repository history begins October 15, 2026, within the contest window. The adaptation began October 16 on a separate branch. The provider, visitor isolation, abuse controls, and deployment work are recorded against the baseline in [CONTEST_CHANGES.md](CONTEST_CHANGES.md). Do not imply that earlier functionality was first written on the hackathon branch.

## Final submission fields

| Field | Value before submission |
| --- | --- |
| Tested public source revision | [0c010c00c160e1cb47c60eea7f758050c23a3831](https://github.com/agammann/easy-street/commit/0c010c00c160e1cb47c60eea7f758050c23a3831), the deployed privacy/configuration follow-up on the [hackathon branch](https://github.com/agammann/easy-street/tree/hackathon/nebius-nemotron-2026); [draft PR #1](https://github.com/agammann/easy-street/pull/1) remains open, not merged/released. [CI run 38999513875](https://github.com/agammann/easy-street/actions/runs/38999513875) fully passed all three OS runners through Python-only ZIP installation. The first funded hosted generation ran on `0e0c17d`; this follow-up changes no provider backend and makes no additional inference claim. Later documentation is separate; see [verification](VERIFICATION.md). |
| Working judging URL | [https://easy-street-agammann-2026.fly.dev](https://easy-street-agammann-2026.fly.dev), deployed with approved bounded funding; private judge-code placement and ongoing operation through December 15 remain gates |
| Public YouTube URL | Pending recording and publication approval |
| Exact Nemotron model and approved live evidence | `nvidia/nemotron-3-super-120b-a12b` verified by the authenticated catalog and three actual local/hosted jobs, including v2.1; owner content acceptance remains pending |
| Contact for access failures | Owner must provide a monitored route |
| Judge credentials | Put only in Devpost's private testing instructions, never this public file |

## Private judge testing instructions template

This section is a template. The URL and observed timing below are real; fill the private access credential and contact before submission; keep any completed credential version out of Git.

1. Open **[Easy Street](https://easy-street-agammann-2026.fly.dev)** in a fresh browser window. Use **[private judging credential supplied in this testing field]** if prompted. No provider account, payment, or personal API key is required.
2. Choose **Generate sample with Nebius** for the one-click original licensed chapter workflow; review its source/provider disclosure and expect variable timing: the observed uncached hosted job completed in **15.8418 seconds**, with no guaranteed wait. It uses preset small-course settings and skips the manual outline steps below.
3. For configurable generation, instead choose **Try the sample chapter**, or upload a chapter you have permission to process. Inspect extraction, choose modules and assessment counts, review the proposed outline/source disclosure, approve, and start generation. The screen identifies Nebius/Nemotron.
4. Open a generated section's source evidence. Compare its statement and quote, inspect review warnings, and edit a sentence. Try regenerating one section.
5. Export learner HTML and the separate answer key. Delete your workspace when finished. Active workspace retention is **24 hours**; normal maintenance removed a deliberately expired hosted test fixture. This did not wait a real 24 hours. Active work may delay cleanup, and the Fly volume reports five-day snapshot retention; application deletion does not instantly erase any backup copies.
6. If access or generation is unavailable, contact **[monitored owner route]**. A spending cutoff pauses generation and needs operator intervention; it must not be presented as normal successful judging.

The testing-access arrangement must stay available without payment or BYO keys through December 15, 2026, noon Pacific, per the [official rules](https://nebiusglobalaihackathon.devpost.com/rules). Publish only instructions that have been exercised from a fresh session.
