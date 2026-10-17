# Easy Street — Devpost draft

Entry draft for review, included on the public hackathon branch. It has not been submitted to Devpost. Replace the remaining verification fields with measured results before using this as the final entry. Two real Nebius runs passed technical checks, including revised prompt v2.1. Separate content inspection still found citation-coverage/precision gaps. Do not portray live integration success as final content acceptance or a working hosted deployment. No Devpost entry was modified or submitted by this preparation.

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

The contest integration adds Nebius Token Factory as a backend provider while preserving OpenAI support. Its configured model is **`nvidia/nemotron-3-super-120b-a12b`**. The authenticated catalog and both approved live runs verified that identifier, including revised prompt v2.1; see [verification](VERIFICATION.md). Owner content review and manual corrections are still required. Token Factory is wired to the actual generation and support-review calls. No web search or external retrieval contributes educational claims. Source passages and outline text are treated as untrusted data, including instructions embedded in a document.

The hosted demo keeps the operator's Nebius key in the server's secret environment. Browsers receive course results and non-secret configuration, never provider credentials. Bounded uploads, module/token limits, duplicate-request handling, concurrency control, and persistent usage accounting constrain operator exposure.

## Challenges

Source quotations are necessary but do not automatically substantiate every sentence that cites them. We kept exact evidence checks separate from semantic support review and made uncertainty visible. We also had to adapt a personal local workspace into isolated temporary visitor workspaces without weakening the original bring-your-own-key installation.

## Accomplishments

- Preserved editable modules, configurable assessments, evidence views, and recovery from the released application.
- Kept provider credentials on the backend and retained source-only course generation.
- Prepared a separately bounded judging configuration and an original sample workflow.
- The corrected public revision passed Linux, Apple Silicon Mac, and Intel Mac CI, including tests, build, packaging, production smoke, and fresh Python-only ZIP installation. Local 512 MiB/0.5 CPU container acceptance also passed with explicit offline content. See [verification](VERIFICATION.md) for exact revision-specific counts and the scope of mocks.
- The first approved live Nebius sample returned ten sections with exact quotations in 8.62 seconds: 5,984 input and 1,397 output tokens, at $0.0030525 estimated from reported usage. Zero automatic review flags did not establish complete support: a separate content inspection found a title-only introduction citation and an unsupported assurance. A second bounded v2.1 run returned ten sections with exact quotations in 10.50 seconds at $0.0041139. It improved the introduction, but citation-coverage and approximation gaps remain. Owner review and manual correction are still required. Aggregate estimated cost across both runs was $0.0071664; see [verification](VERIFICATION.md).

## What we learned

An educational generation tool needs clear source boundaries, recovery, and readable review controls as much as model output. A model can preserve an exact quotation while adding a claim the quotation does not establish. The tool therefore supports human inspection rather than asserting that automated checks guarantee correctness.

## What's next

Evaluate broader subject matter and longer sources using material we may legally process. Improve support-review quality using reproducible cases while preserving uncertainty. Broader classroom workflows, grading, and LMS integration remain future work rather than claims about this build.

## Track and technologies

Best Apps and Agents. React, TypeScript, FastAPI, SQLite, Nebius Token Factory, NVIDIA Nemotron, OpenAI-compatible SDK, PDF/DOCX/TXT extraction. Add only services actually used in the approved deployment.

## Nebius and NVIDIA feedback

Observed in the first approved sample: Token Factory accepted the configured Nemotron model and returned schema-valid generation and support-review responses. The complete ten-section job took 8.62 seconds and reported 5,984 input / 1,397 output tokens. Exact quotations were retained. However, the support review returned zero flags while a separate inspection found a title-only factual citation and stronger assurance wording than the chapter supports. Revised prompt v2.1 and a new cache identity completed a second real sample in 10.50 seconds, reporting 8,079 input / 1,878 output tokens. Its introduction cites substantive source material and no longer adds the absorption guarantee. Separate inspection still found citation-coverage and approximation gaps despite zero automatic flags. These two small samples verify the integration and expose review limits; they are not a platform-wide quality or latency benchmark. Final feedback should add actual hosting results.

## Existing project and contest changes

Easy Street v1.0.0 existed before this hackathon adaptation. Its repository history begins October 15, 2026, within the contest window. The adaptation began October 16 on a separate branch. The provider, visitor isolation, abuse controls, and deployment work are recorded against the baseline in [CONTEST_CHANGES.md](CONTEST_CHANGES.md). Do not imply that earlier functionality was first written on the hackathon branch.

## Final submission fields

| Field | Value before submission |
| --- | --- |
| Tested public source revision | [1f75aa907e647b06bb416b4ae13536281842aaf9](https://github.com/agammann/easy-street/commit/1f75aa907e647b06bb416b4ae13536281842aaf9), published on the [hackathon branch](https://github.com/agammann/easy-street/tree/hackathon/nebius-nemotron-2026); [draft PR #1](https://github.com/agammann/easy-street/pull/1) open, not merged/released. [CI run 38995934439](https://github.com/agammann/easy-street/actions/runs/38995934439) fully passed. Subsequent operational/prompt edits need their own final revision and checks; see [verification](VERIFICATION.md). |
| Working judging URL | Fly/$15 approved through December 15; deployment conditional on final checks and a passing live Nebius test, not yet performed |
| Public YouTube URL | Pending recording and publication approval |
| Exact Nemotron model and approved live evidence | `nvidia/nemotron-3-super-120b-a12b` verified by the authenticated catalog and two approved real runs, including v2.1; owner content review/correction and deployed acceptance pending |
| Contact for access failures | Owner must provide a monitored route |
| Judge credentials | Put only in Devpost's private testing instructions, never this public file |

## Private judge testing instructions template

This section is a template. Fill in the actual URL, access credential, contact, and verified timings after deployment; keep any completed credential version out of Git.

1. Open **[approved judging URL]** in a fresh browser window. Use **[private judging credential supplied in this testing field]** if prompted. No provider account, payment, or personal API key is required.
2. Choose **Generate sample with Nebius** for the one-click original licensed chapter workflow; review its source/provider disclosure and allow **[measured time]** for the uncached run. It uses preset small-course settings and skips the manual outline steps below.
3. For configurable generation, instead choose **Try the sample chapter**, or upload a chapter you have permission to process. Inspect extraction, choose modules and assessment counts, review the proposed outline/source disclosure, approve, and start generation. The screen identifies Nebius/Nemotron.
4. Open a generated section's source evidence. Compare its statement and quote, inspect review warnings, and edit a sentence. Try regenerating one section.
5. Export learner HTML and the separate answer key. Delete your workspace when finished. Active uploaded documents and results expire after **[actual configured retention]**; disclose the approved host's separate backup retention here before submission.
6. If access or generation is unavailable, contact **[monitored owner route]**. A spending cutoff pauses generation and needs operator intervention; it must not be presented as normal successful judging.

The testing-access arrangement must stay available without payment or BYO keys through December 15, 2026, noon Pacific, per the [official rules](https://nebiusglobalaihackathon.devpost.com/rules). Publish only instructions that have been exercised from a fresh session.
