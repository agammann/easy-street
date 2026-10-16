# Easy Street verification report

Verification date: October 15, 2026.

## Release status

This is a development preview of the single-chapter workflow. The local application, deterministic offline demo, automated provider-boundary tests, and browser workflow have been exercised. **Real OpenAI generation remains unverified.** No paid provider requests were made during this verification. Secure credential setup is pending; a live generation and regeneration run followed by a source-support review is still required before declaring the complete first milestone verified.

## Automated checks

| Check | Result |
| --- | --- |
| Backend unit and independent API integration suite | 53 passed |
| React frontend tests | 8 passed |
| TypeScript and production Vite build | Passed |
| Frontend production and development dependency audit | No known vulnerabilities reported at verification time |
| Publication file review | No real credentials, private workspace paths, private documents, or runtime databases found in the publication set |

The backend suite emits one non-failing upstream Starlette warning about its deprecated HTTPX test transport. Automated tests use the original fixture and deterministic or fake provider responses. They do not establish live model quality.

Backend coverage includes PDF/TXT extraction, stable locations and extraction caching; invalid and streamed oversized uploads; approval and count validation; exact quotation resolution; missing and conflicting evidence; malformed responses; duplicate jobs; concurrent work; bounded retries; budget reservations; uncertain timeouts; cancellation; restart recovery; manual edits, reordering and version preservation; separate exports; HTML escaping; and Host, Origin and fetch-metadata restrictions.

Provider-boundary tests confirm that supplied document content remains separate from application instructions, provider tools are disabled, automatic retries are disabled, and requests use `store=False`. They do not prove that a live model always resists instructions embedded in documents. Human review remains necessary.

Frontend regressions cover the terminal-job transition into the completed course, generation gates, persistence and edit protections, answer separation, source inspection, oversized uploads, and recoverable save failures.

## Browser verification

The production frontend was served by the localhost FastAPI process and tested in a real browser.

- Original TXT sample: passage-by-passage extraction preview, course options, approved outline, explicit zero-cost offline generation, completed course review.
- Original PDF upload: local extraction, accurate Page 1 location, readable preview, coverage warnings, editable title, locally prepared outline, and clear missing-key guidance before generation.
- Evidence: source modal displayed the quotation and location, with the complete supporting passage available on demand.
- Editing: navigation was blocked while an edit was unsaved; a saved manual announcement survived refresh, reordering, and regeneration of another section.
- Recovery and history: the completed generation opened the editor, and a saved historical version showed the prior announcement text.
- Assessment separation: the learner view hid quiz answers and explanations; the answer-key view showed them. Detailed quiz review notes are also separated to avoid leaking answers.
- Downloads: learner HTML, separate answer-key HTML, and structured JSON were downloaded through their visible controls. The learner export retained source locations and omitted quiz answer text and answer-revealing evidence quotations.
- Visual review: desktop and 390-pixel mobile layouts were inspected against the selected visual direction. Home and course-editor layouts were also checked at 320 pixels; neither produced document-level horizontal overflow after the responsive fixes. No browser warnings or errors were recorded in the final check. The interface uses local artwork and system fonts.

## Limits and follow-up

- Live API generation, provider-reported usage on a real request, live factual support and usefulness, and live regeneration need the pending credential setup and subsequent review.
- The release supports one module, one written assignment, one rubric, and one quiz with one to five questions. Larger books and multiple modules are deferred.
- Readable PDF and UTF-8 TXT are supported. DOCX, selective OCR, scanned-document interpretation, and reliable table/equation interpretation are deferred.
- HTML and JSON are export formats. JSON import/restore is not implemented; keep local database and document backups.
- Source checks help identify mistakes but cannot guarantee accuracy. Suggested objectives, activities, schedules and rubrics are proposals.
- The app is a personal localhost workspace without multi-user authentication. Public hosting is outside this release.
- Local cost controls are conservative application limits, not provider-enforced billing caps. An in-flight or uncertain request can still incur charges.
- Dependency/license review covers the installed dependency graphs; optional platform binaries beyond the tested Windows environment were not individually downloaded. See [DEPENDENCIES.md](docs/DEPENDENCIES.md).

Reproduce the automated checks using the commands in [README.md](README.md). The GitHub Actions workflow runs the backend suite, frontend tests and production build on Ubuntu; consult the repository's current Actions result for the remote status of a particular revision.
