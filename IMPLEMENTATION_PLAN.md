# Easy Street implementation plan

Build a local-first, single-chapter milestone before extending to full books. React and TypeScript provide the browser interface; one FastAPI backend serves the production build, extracts documents locally, and persists documents, courses, versions, jobs, and usage in SQLite.

1. Establish the source model, guarded localhost API, PDF extraction, and an original sample chapter.
2. Implement an outline approval gate, bounded provider calls, evidence validation and review, persistent generation jobs, and an explicit offline demo.
3. Build a responsive course workspace with extraction preview, course options, source inspection, editing, section regeneration, version preservation, and learner/answer/JSON exports.
4. Test backend and frontend behavior, inspect desktop/mobile browser flows, and run the actual OpenAI path within a confirmed development spending cap.
5. Review dependencies, exclude private runtime data and credentials, add installation/privacy/limitations documentation, and publish the tested source to GitHub.

Acceptance criteria:

- A readable chapter PDF produces stable page-linked passages and an extraction preview before generation. Unreadable content is flagged; no paid OCR is used.
- Generation requires explicit outline approval and disclosure that selected passages go to OpenAI. The first milestone enforces one module, one assignment, and one quiz, with a configurable question count.
- Generated factual content has resolvable evidence, a separate support check, and visible review flags. Missing support is never represented as verified.
- API keys remain in backend environment configuration. Upload limits, origin/host validation, escaped rendering, and safe errors protect local use.
- Cost reservations cover output limits and verification calls; actual reported usage is saved. Duplicate jobs, cancellation, uncertain requests, and restart recovery have explicit states and bounded behavior.
- Manual edits and saved versions survive regeneration and restart. Learner HTML excludes answers; answer-key HTML and structured JSON are separate, with source text excluded by default.
- Tests, real-provider verification status, and remaining limits are reported accurately before publication.

Deferred: full-book/multi-module generation, DOCX support, selective OCR, hosted accounts, LMS integrations, automatic grading, additional providers, and public web deployment.
