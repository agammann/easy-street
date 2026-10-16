# Easy Street verification report

Verification date: October 15, 2026.

## Release status

The single-chapter workflow has been exercised with both the deterministic offline sample and real OpenAI requests using the original included PDF. Live generation, separate support verification, targeted regeneration, editing, cached reuse, persistence, and exports passed the final integration checks. Manual content review found unsupported wording missed by the verifier; the reviewed example was corrected through the normal edit API. This is a small local-first release, not a guarantee of factual accuracy or a full-book quality evaluation.

## Automated checks

| Check | Result |
| --- | --- |
| Backend unit and independent API integration suite | 81 passed |
| React frontend tests | 8 passed |
| TypeScript and production Vite build | Passed |
| Frontend production and development dependency audit | No known vulnerabilities reported at verification time |
| Publication file review | No real credentials, private workspace paths, private documents, or runtime databases found in the publication set |
| Live provider acceptance | 24 checks passed on the original PDF |
| Independent local evidence-catalog audit | 27 checks passed |

The backend suite emits one non-failing upstream Starlette warning about its deprecated HTTPX test transport. Automated tests use the original fixture and deterministic or fake provider responses. They do not establish live model quality.

Backend coverage includes PDF/TXT extraction, stable locations and extraction caching; invalid and streamed oversized uploads; approval and count validation; exact quotation resolution; missing and conflicting evidence; malformed responses; duplicate jobs; concurrent work; bounded retries; budget reservations; uncertain timeouts; cancellation; restart recovery; manual edits, reordering and version preservation; separate exports; HTML escaping; and Host, Origin and fetch-metadata restrictions.

Provider-boundary tests confirm that supplied document content remains separate from application instructions, provider tools are disabled, automatic retries are disabled, and requests use `store=False`. They do not prove that a live model always resists instructions embedded in documents. Human review remains necessary.

The evidence catalog preserves the complete selected source as bounded, contiguous excerpts. The model selects allowed IDs, and application code expands them into original quotations. Unknown IDs and oversized catalogs are rejected. Targeted regeneration uses a schema restricted to one section with its existing ID and kind. Cost bounds include the catalog, response schema, and evidence expansion needed for verification.

Frontend regressions cover the terminal-job transition into the completed course, generation gates, persistence and edit protections, answer separation, source inspection, oversized uploads, and recoverable save failures.

## Live provider verification

The final run used `gpt-4.1-mini`, prompt version `easy-street-1.3`, and the included one-page Small Garden Watering PDF. It generated one module, one assignment with a rubric, and three quiz questions with answers and explanations. Every returned quotation resolved to an exact original source span. A subsequent notes-only regeneration completed and preserved an unrelated manual announcement edit; the original notes remained in version history, and dependent assessments were marked for review.

A repeated course with identical inputs reused cached results without adding provider usage. Learner HTML excluded a deliberately inserted private answer marker while the separate answer key included it. The marker was then removed. Exports retained the cached document's original filename and Page 1 location, JSON omitted the full source text, and an application restart preserved the manual edit.

| Final run stage | Input tokens | Output tokens | Calculated cost |
| --- | ---: | ---: | ---: |
| Course generation | 2,043 | 1,220 | $0.0027692 |
| Course support verification | 4,419 | 489 | $0.0025500 |
| Notes regeneration | 2,350 | 236 | $0.0013176 |
| Notes support verification | 1,530 | 105 | $0.0007800 |
| Final run total | 10,342 | 2,050 | $0.0074168 |

All development attempts together used 11 provider calls and had a calculated cost of **$0.0257092**, below the approved $10 cap, with no unresolved reservations. These costs use provider-reported token counts and the documented full input rate; they are application estimates, not a provider invoice.

Earlier live attempts exposed two recoverable integration problems: the model synthesized quotations instead of copying exact spans, and a notes regeneration returned the entire course. The first led to the evidence catalog; the second led to the restricted regeneration schema. Invalid output was stopped without automatic retries, and the saved course was preserved. The final export test also corrected a test assumption: extraction caching correctly retained the original filename rather than adopting a later upload alias. No additional provider call was needed for that correction.

Manual review remains material. The provider and its separate verifier both accepted some unsupported claims about preventing overwatering, ensuring proper moisture, and benefits absent from the source. The final example removes those claims, retains source uncertainty, and replaces internal excerpt IDs appearing in prose with readable explanations. Those corrections are saved edits, not evidence that the verifier reliably detects such mistakes. The quiz answers matched the source; the assignment and rubric form a usable practice exercise, while objectives and grading criteria remain labeled proposals. Broader subjects, difficult documents, repeated quality measurements, and adversarial live tests remain unverified.

## Browser verification

The production frontend was served by the localhost FastAPI process and tested in a real browser.

- Original TXT sample: passage-by-passage extraction preview, course options, approved outline, explicit zero-cost offline generation, completed course review.
- Original PDF upload: local extraction, accurate Page 1 location, readable preview, coverage warnings, editable title, locally prepared outline, and clear missing-key guidance before generation.
- Evidence: source modal displayed the quotation and location, with the complete supporting passage available on demand.
- Editing: navigation was blocked while an edit was unsaved; a saved manual announcement survived refresh, reordering, and regeneration of another section.
- Recovery and history: the completed generation opened the editor, and a saved historical version showed the prior announcement text.
- Assessment separation: the learner view hid quiz answers and explanations; the answer-key view showed them. Detailed quiz review notes are also separated to avoid leaking answers.
- Downloads: learner HTML, separate answer-key HTML, and structured JSON were downloaded through their visible controls. The learner export retained source locations and omitted quiz answer text and answer-revealing evidence quotations.
- Live follow-up: the saved, corrected provider-generated course was reopened in the browser with its edit flags visible, and all three exports were downloaded again through the visible controls.
- Visual review: desktop and 390-pixel mobile layouts were inspected against the selected visual direction. Home and course-editor layouts were also checked at 320 pixels; neither produced document-level horizontal overflow after the responsive fixes. No browser warnings or errors were recorded in the final check. The interface uses local artwork and system fonts.

## Limits and follow-up

- Live API testing covered one small original PDF and one model. It establishes this workflow's operation, not consistent quality across arbitrary textbooks or resistance to every instruction embedded in uploaded content.
- The release supports one module, one written assignment, one rubric, and one quiz with one to five questions. Larger books and multiple modules are deferred.
- Readable PDF and UTF-8 TXT are supported. DOCX, selective OCR, scanned-document interpretation, and reliable table/equation interpretation are deferred.
- HTML and JSON are export formats. JSON import/restore is not implemented; keep local database and document backups.
- Source checks help identify mistakes but cannot guarantee accuracy. Suggested objectives, activities, schedules and rubrics are proposals.
- The app is a personal localhost workspace without multi-user authentication. Public hosting is outside this release.
- Local cost controls are conservative application limits, not provider-enforced billing caps. An in-flight or uncertain request can still incur charges.
- Dependency/license review covers the installed dependency graphs; optional platform binaries beyond the tested Windows environment were not individually downloaded. See [DEPENDENCIES.md](docs/DEPENDENCIES.md).

Reproduce the automated checks using the commands in [README.md](README.md). The GitHub Actions workflow runs the backend suite, frontend tests and production build on Ubuntu; consult the repository's current Actions result for the remote status of a particular revision.
