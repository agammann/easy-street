# Easy Street

**Big ideas. Your own way.**

Turn a chapter you already have into an editable personal course. Easy Street runs on your computer: preview the extracted material, approve a proposed outline, then build a lesson, a written assignment with a rubric, and a quiz with a separate answer key.

![An open book becomes a road through colorful hills](frontend/public/learning-road.png)

Easy Street is free software under the MIT license. **You bring your own OpenAI API key and pay OpenAI directly for usage.** There is no bundled developer key, shared billing account, subscription, or required hosted service.

**Single-chapter milestone:** the local workflow, offline demo, and real OpenAI generation and section regeneration have been tested with the included original PDF. Live review also found unsupported wording that the automated verifier missed; review and editing remain required. See the [completion report](COMPLETION_REPORT.md) for the evidence and limitations.

## First milestone

- Upload a readable PDF or UTF-8 TXT chapter and inspect the locally extracted passages.
- Use stable PDF page references and TXT paragraph references. Text files never receive invented page numbers.
- Review a locally proposed outline, choose the difficulty and one to five quiz questions, and approve the outline before generation.
- Generate one module, one written assignment, one rubric, and one quiz. All assessment counts are course-wide totals.
- Inspect original supporting quotations with **Show source**. The provider selects bounded excerpt IDs; the application inserts the corresponding source text. A separate provider call reviews factual support; missing evidence and detected conflicts are flagged for your review.
- Edit and reorder sections, save versions, and regenerate an individual section.
- Export learner HTML, a separate answer key, or a structured JSON backup.
- Try the included original sample in **Offline demo** mode without a key or network call.

This release deliberately limits each course to one module, one written assignment, and one quiz. Multi-module books, DOCX, selective OCR, additional providers, LMS integration, and automatic grading are future work. The demo uses fixed sample content; it does not demonstrate live model quality.

## Install and run

Requires Python 3.11 or newer and Node.js 22.12 or newer. Docker, local models, and a vector database are not required.

```sh
git clone https://github.com/agammann/easy-street.git
cd easy-street
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Install the backend and build the browser app:

```sh
python -m pip install -r backend/requirements-lock.txt
cd frontend
npm install
npm run build
cd ..
python start.py
```

Open **http://127.0.0.1:8000**. The Python server serves both the API and the built frontend. After installing dependencies, the offline sample runs without a provider connection.

### Configure your own provider

The backend reads `OPENAI_API_KEY` from its environment or the ignored `.env.local` file. Use the secure OpenAI key setup flow when working in Codex. For an ordinary installation, copy `.env.example` to `.env.local` and configure your own key locally with a trusted editor. Never paste it into chat, a browser form, a course, or a GitHub issue. Restart the server after changing configuration.

The example file contains **no key**. Keys never belong in frontend code, browser storage, SQLite, exports, or screenshots. Easy Street has no saved-key feature or key-entry web form. Environment files are local secrets and must be protected by your operating-system account and backup practices.

Local state lives in `data/` by default. To choose another directory, set `EASY_STREET_DATA_DIR` before startup. Keep the database, original-file directory, and environment secrets out of source control. The JSON export does not replace a backup of your local database and documents.

Set `EASY_STREET_BUDGET_USD` to the application spending limit you want for this local database. The default is $1. The Settings screen reports whether a key is configured, pricing assumptions, remaining allowance, and recorded usage.

### Development

Run the FastAPI backend on port 8000 and Vite on port 5173 in separate terminals. Vite is only a frontend development server; it proxies `/api` to the one Python backend.

```sh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```sh
cd frontend
npm run dev -- --host 127.0.0.1
```

The production startup command binds to localhost. Do not expose this application to a public network; it is a personal local workspace without multi-user authentication.

## Privacy and source support

Original files, extracted text, courses, versions, jobs, and usage records are stored locally. Extraction and outline preparation do not send documents to OpenAI. When you approve generation, **selected text excerpts and the requested course structure are sent to OpenAI**, followed by a verification request containing the relevant excerpts and generated content. Requests use `store=False`; provider processing is still subject to the provider's policies. There is no web search or outside retrieval in course generation.

Uploaded text is untrusted data. Embedded instructions are not intended to become application instructions, and the generation provider has no browsing, file, or execution tools. The application checks section counts, source IDs, and exact quotation matches, then asks the provider to check factual support. These checks reduce mistakes; **they cannot guarantee correct or perfectly grounded content**. Read the source and review the course before relying on it or sharing it. Structure, objectives, assignments, announcements, and rubrics are proposals, not textbook policies or accreditation.

PDF layout extraction can miss tables, figures, equations, or scanned content. Warnings and a preview make this visible. This release does not perform OCR or silently invoke a paid vision service. Uploads are bounded to 15 MiB, 100 PDF pages, and 250,000 extracted characters. Generation uses a smaller bounded selection of excerpts; review its coverage before approving.

Use material you have permission to process. Exports omit the original document and complete extracted source by default, but can contain short supporting quotations from your material. The JSON backup includes the answer key; share learner HTML when answers should remain separate. A JSON backup is an export format in this milestone, not an implemented import/restore flow.

## Costs and recovery

The default provider model is `gpt-4.1-mini`. Pricing checked **October 15, 2026**: $0.40 per million input tokens, $0.10 per million cached input tokens, and $1.60 per million output tokens. See the [official model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini) and [Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

Before generation, Easy Street shows a conservative estimate that includes maximum output and the support-verification call. It reserves budget before scheduling work and records provider-reported token usage afterward. Cost calculations use the full input rate conservatively, so provider cache discounts may reduce the actual bill. The local budget is an application guard, **not a provider-enforced billing guarantee**.

Jobs persist in SQLite, and duplicate submissions reuse their job identity. Provider SDK automatic retries are disabled. If a timeout or process interruption leaves a request outcome uncertain, Easy Street preserves its reservation and does not silently repeat the paid request. Cancellation stops later work but cannot guarantee that an in-flight request stops or avoids charges. Review an uncertain request in your provider dashboard before deliberately starting another.

## Tests and release status

```sh
python -m pytest backend/tests tests/integration
cd frontend
npm test
npm run build
```

See [COMPLETION_REPORT.md](COMPLETION_REPORT.md) for the exact verification results and live API status of this release. Tests use deterministic fixtures and fake provider responses unless explicitly identified as live. API behavior is documented in [backend/API_CONTRACT.md](backend/API_CONTRACT.md). The Python dependency snapshot is in `backend/requirements-lock.txt`; the frontend snapshot is in `frontend/pnpm-lock.yaml`. Use `pnpm install --frozen-lockfile` instead of `npm install` to reproduce the verified frontend dependency graph exactly.

Project source is MIT licensed. Dependencies retain their own licenses; see [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).

## Troubleshooting

- **The browser page is missing:** run the frontend build before `python start.py`.
- **The provider is unavailable:** configure your own backend key, check your provider account access and billing, then restart. The offline sample remains available.
- **Budget exhausted:** check Settings and uncertain reservations before raising the local limit. Changing the cap does not change provider-side billing controls.
- **Unreadable PDF:** use a text-based PDF, a smaller chapter, or a locally OCR-processed copy. Encrypted PDFs are rejected.
- **A section needs review:** open its source references, correct unsupported text, and keep manual edits. Regeneration saves a previous version and marks dependent material for review.
- **Cross-origin request blocked:** use `127.0.0.1:8000` in production or the documented Vite development origin. Do not disable origin protection to embed the app in another website.

Easy Street is a working product name; domain and trademark availability have not been verified.
