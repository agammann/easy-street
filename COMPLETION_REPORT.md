# Easy Street 1.0.0 verification report

This report records the release workflow checks and the limits of their evidence. Easy Street provides a usable local course workflow, with human review required for generated content.

## Release scope

- PDF, DOCX, and UTF-8 TXT extraction, with previews and stable page or paragraph references. Uploads are limited to 15 MiB, 100 PDF pages, and 250,000 extracted characters. DOCX preserves paragraph locations without inventing page numbers.
- One to six modules; zero to six assignments and zero to six quizzes across the course, with at most two of each per module. Each quiz has one to five questions, separate answers, and explanations. Assignments include proposed rubrics.
- Editable module objectives, titles, assessment distribution, and source selection. Automatic plans fit 24,000 source characters and 512 evidence excerpts per module. Omitted source passages are explicitly reported before approval.
- Generation and separate evidence review per module, targeted section regeneration, cancellation, cached reuse, persistent checkpoints, and safe restart recovery. Requests with uncertain outcomes are not automatically repeated.
- Section editing and reordering, version restore, archive/unarchive, printable learner HTML, a separate answer key, and JSON backup import. Imports create a new course, mark content for review, and allow editing and export without the original document. Reattaching the exact source enables evidence inspection and generation.
- Optional local English OCR for up to five explicitly selected PDF pages. OCR uses Tesseract and PDFium locally, has process time limits, and never invokes paid vision. Recognition needs comparison with the original pages.
- A downloadable ZIP containing the built interface, a Python 3.12 launcher, and private terminal configuration. End users do not need Git or Node.js for that release asset; source checkouts still require a frontend build.

## Current automated results

| Check | Result |
| --- | --- |
| Backend and independent integration tests | **136 passed, 1 skipped** on Windows |
| Frontend and API-client tests | **35 passed** |
| TypeScript and production frontend build | **Passed** |
| Actual PDFium rendering on Windows | **Passed** |
| Actual local Tesseract recognition on Windows | **Not run:** Tesseract is unavailable locally |
| Fresh downloadable ZIP installation and startup | **Passed on Windows:** clean Python environment, real launcher, built assets, offline workflow, exports, restart persistence, no key and zero usage |
| Ubuntu and macOS CI workflow | **Publication gate:** all three operating-system jobs must pass on the release revision |

The backend skip is the real OCR integration test. One non-failing Starlette warning concerns its deprecated HTTPX test transport. Automated tests use deterministic fixtures or fake providers and do not establish model quality.

Regression coverage includes bounded document parsing, stable OCR variants, module and assessment counts, complete evidence catalogs, generation approval, idempotency, cost reservations, cancellation races, uncertain outcomes, module checkpoint recovery, cached generation without a key, preservation of edits during regeneration, version restore, backup/source recovery, and answer separation. Automatic planning now accounts for actual evidence-excerpt counts, and outline changes refresh both section and course review flags. JSON backups retain selected and cited source locations while omitting unused references so large documents remain recoverable. Offline demonstrations prefer substantive source passages over short headings while retaining approved reading references.

The workflow targets Ubuntu and macOS 15 on Apple Silicon and Intel. It installs dependencies, runs both suites, builds the interface, checks production startup, packages the app, and tests installation from that ZIP. Ubuntu additionally installs Tesseract and runs the real local OCR check. Consult the [Actions result for the exact revision](https://github.com/agammann/easy-street/actions); release publication requires a successful run for that commit. CI receives no API key. Hosted checks establish automated setup and localhost behavior, not interactive Safari or macOS desktop-launch behavior.

## Current live provider verification

The current gpt-4.1-mini integration, using prompt version easy-street-2.0, was exercised with the original garden chapter as a DOCX. Two modules produced **18 sections** through four generation/verification calls. A targeted regeneration of module two's notes used two further calls and preserved the entire first module, including its manual corrections.

Every checked evidence quotation matched an exact original source span. That did not guarantee factual support: manual review identified **six sections** needing corrections for unsupported plant-health claims, overstrong benefits, or conclusions about information absent from the source. Those sections were edited. This is direct evidence that the separate verifier can miss unsupported wording.

An identical two-module course then reused cached results, produced all 18 sections, and added **zero provider usage**. The six new live calls had a calculated cost of **$0.0102792**. Including earlier development checks, calculated spending is **$0.0359884**, with **$0 reserved** at verification. These calculations use provider-reported tokens and the documented rates; they are not a provider invoice or provider-enforced billing limit.

## Current browser verification

The production app was exercised in a real browser:

- Created and completed a two-module, 18-section offline course through the visible source preview, options, approval, and generation controls.
- Saved an edit and restored an earlier version, preserving a recoverable record of the newer work.
- Imported a JSON course without its source, then reattached the exact original DOCX.
- Confirmed learner quizzes hide answers and answer-revealing evidence quotations, while the answer-key view reveals them for review.
- Archived and unarchived a course.
- Inspected the 390-pixel layout without document-level horizontal overflow.
- Reapproved a completed course's outline without repeating generation, downloaded learner HTML, and recorded no browser warnings or errors in the final check.

## Prior coverage and remaining limits

Earlier revisions were tested with the original one-page PDF through live generation, separate verification, targeted regeneration, manual editing, cached reuse, persistence, and all three exports. Earlier clean Windows source installations and hosted macOS setup checks also passed. Those results provide historical coverage; they do not replace fresh verification of the current release archive or revision.

Current live quality testing covers a small original garden chapter and one model. It does not establish reliable quality across arbitrary textbooks, difficult scans, other subjects, or adversarial document instructions. Exact quotations and source locations help review; they do not prove that a claim follows from the cited material. Suggested objectives, tasks, and rubrics remain proposals.

PDF/DOCX extraction and OCR do not reliably interpret images, tables, equations, or complex layouts. Interactive Safari behavior, macOS desktop installer behavior, and actual Windows OCR recognition remain unverified. The app is a personal localhost workspace without multi-user authentication; public hosting is outside this release. In-flight or uncertain provider requests may still incur charges.

Reproduction commands and operating instructions are in [README.md](README.md). Dependency and redistribution notes are in [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).
