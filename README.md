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

Install **Git, Python 3.12, and Node.js 22.12 or newer** first. The commands below install pnpm 10 and use the committed dependency snapshots. Docker, local models, and a vector database are not required. Installation needs internet access; the included offline demo does not need an API key.

### Windows PowerShell

Run these commands in PowerShell. They call the virtual environment's Python directly, so activating a script or changing PowerShell's execution policy is unnecessary.

```powershell
git clone https://github.com/agammann/easy-street.git
Set-Location easy-street
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
npm.cmd install --global pnpm@10
Set-Location frontend
pnpm.cmd install --frozen-lockfile
pnpm.cmd build
Set-Location ..
.\.venv\Scripts\python.exe start.py
```

If `py` is unavailable, use `python -m venv .venv` after checking that `python --version` reports Python 3.12. If a command is not found after installing Python or Node.js, open a new terminal so it receives the updated PATH.

### macOS or Linux shell

Use a Python 3.12 installation for `python3` in these commands:

```sh
git clone https://github.com/agammann/easy-street.git
cd easy-street
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-lock.txt
npm install --global pnpm@10
cd frontend
pnpm install --frozen-lockfile
pnpm build
cd ..
.venv/bin/python start.py
```

The clean install was checked on Windows with Python 3.12.14, Node.js 24.19.0, and pnpm 10.34.7. The repository's automated workflow targets Ubuntu with Python 3.12 and Node.js 22; macOS desktop startup has not been tested. See the [completion report](COMPLETION_REPORT.md) for the current results.

Open **http://127.0.0.1:8000** manually in your browser and leave the terminal running. The Python server serves both the API and the built frontend. Press **Ctrl+C** in that terminal to stop it. To return later, run the final Python startup command again from the repository root; reinstalling or rebuilding is unnecessary unless dependencies or frontend source changed.

### Try a course without an API key

1. Choose **Try the sample chapter** on the start page.
2. Inspect the extracted passages, then choose **Looks good. Shape my course**.
3. Keep **Offline demo** selected, choose one to five quiz questions, and select **Preview my outline**.
4. Review the outline and check its approval box. Select **Review cost & generate**, confirm the estimate is **$0.00**, then select **Approve & generate**.
5. Select **Review my course**. Try **Show source**, edit a section, and export learner HTML or the separate answer key. **My courses** lets you return to the saved course after a restart.

Offline demo uses fixed content for the included sample only. Generating a course from your own PDF or TXT requires the provider setup below. Uploading a document and preparing its outline remain local and free.

### Configure your own provider

The backend reads `OPENAI_API_KEY` from its environment or the ignored `.env.local` file. Use the secure OpenAI key setup flow when working in Codex. For an ordinary installation, copy `.env.example` to `.env.local` in the repository root and configure your own key locally with a trusted editor. In PowerShell, use `Copy-Item .env.example .env.local`; in a macOS/Linux shell, use `cp .env.example .env.local`. Only copy it when you do not already have `.env.local`, so you do not overwrite existing settings. Never paste a key into chat, a browser form, a course, or a GitHub issue. Restart the server after changing configuration, then check **Settings** for the configured-key indicator.

The example file contains **no key**. Keys never belong in frontend code, browser storage, SQLite, exports, or screenshots. Easy Street has no saved-key feature or key-entry web form. Environment files are local secrets and must be protected by your operating-system account and backup practices.

Local state lives in `data/` by default. To choose another directory, set `EASY_STREET_DATA_DIR` before startup. **Run only one backend server process per data directory**, so job recovery belongs to that server. Stop the production server before starting a development backend against the same data. Keep the database, original-file directory, and environment secrets out of source control. The JSON export does not replace a backup of your local database and documents.

Set `EASY_STREET_BUDGET_USD` in `.env.local` or the server environment to the application spending limit you want for this local database. The default is $1. The Settings screen reports whether a key is configured, pricing assumptions, remaining allowance, and recorded usage. This is a cumulative local allowance, not a per-course or daily limit. Review the estimate before approving each generation or regeneration.

### Development

After installing dependencies, stop any running `start.py` server. Run the FastAPI backend on port 8000 and Vite on port 5173 in separate terminals. Vite is only a frontend development server; it proxies `/api` to the one Python backend.

Windows, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal, from the repository root:

```powershell
Set-Location frontend
pnpm.cmd dev
```

On macOS/Linux, use `.venv/bin/python` for the backend command and `cd frontend` followed by `pnpm dev` for the frontend. Open **http://127.0.0.1:5173** for development. After frontend changes, run `pnpm build` in `frontend/` before returning to `start.py`.

The production startup command binds to localhost. Keep the documented ports for the supplied origin protections. Do not expose this application to a public network; it is a personal local workspace without multi-user authentication.

## Privacy and source support

Original files, extracted text, courses, versions, jobs, and usage records are stored locally. Extraction and outline preparation do not send documents to OpenAI. When you approve generation, **selected text excerpts and the requested course structure are sent to OpenAI**, followed by a verification request containing the relevant excerpts and generated content. Requests use `store=False`; provider processing is still subject to the provider's policies. There is no web search or outside retrieval in course generation.

Uploaded text is untrusted data. Embedded instructions are not intended to become application instructions, and the generation provider has no browsing, file, or execution tools. The application checks section counts, source IDs, and exact quotation matches, then asks the provider to check factual support. These checks reduce mistakes; **they cannot guarantee correct or perfectly grounded content**. Read the source and review the course before relying on it or sharing it. Structure, objectives, assignments, announcements, and rubrics are proposals, not textbook policies or accreditation.

PDF layout extraction can miss tables, figures, equations, or scanned content. Warnings and a preview make this visible. This release does not perform OCR or silently invoke a paid vision service. Uploads are bounded to 15 MiB, 100 PDF pages, and 250,000 extracted characters. Generation uses a smaller bounded selection of excerpts; review its coverage before approving.

Use material you have permission to process. Exports omit the original document and complete extracted source by default, but can contain short supporting quotations from your material. The JSON backup includes the answer key; share learner HTML when answers should remain separate. A JSON backup is an export format in this milestone, not an implemented import/restore flow.

## Costs and recovery

The default provider model is `gpt-4.1-mini`. Pricing checked **October 15, 2026**: $0.40 per million input tokens, $0.10 per million cached input tokens, and $1.60 per million output tokens. See the [official model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini) and [Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

Before generation, Easy Street shows a conservative estimate that includes maximum output and the support-verification call. It reserves budget before scheduling work and records provider-reported token usage afterward. Cost calculations use the full input rate conservatively, so provider cache discounts may reduce the actual bill. The local budget is an application guard, **not a provider-enforced billing guarantee**.

Jobs persist in SQLite, and duplicate submissions reuse their job identity. Provider SDK automatic retries are disabled. If a timeout or process interruption leaves a request outcome uncertain, Easy Street preserves its reservation and does not silently repeat the paid request. Cancellation stops later work but cannot guarantee that an in-flight request stops or avoids charges. Review an uncertain request in your provider dashboard before deliberately starting another.

After a browser refresh or server restart, open **My courses** and select the saved course to return to its latest job. An **interrupted** job offers **Resume safely**; the backend checks that no provider request has an uncertain outcome and reuses saved completed stages. An **uncertain** job has no resume action because repeating it could duplicate a paid request. Use **Return to saved course** to review preserved work, and check provider usage before deciding what to do next. A **complete** job offers **Review my course**.

## Tests and release status

After installation, run from the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests tests/integration
Set-Location frontend
pnpm.cmd test
pnpm.cmd build
Set-Location ..
```

On macOS/Linux, use:

```sh
.venv/bin/python -m pytest backend/tests tests/integration
cd frontend
pnpm test
pnpm build
cd ..
```

These test commands do not require an API key or make paid provider calls. They use deterministic fixtures and fake provider responses. A test-suite pass is separate from a live provider-quality review. See [COMPLETION_REPORT.md](COMPLETION_REPORT.md) for the exact verification results and live API status of this release. API behavior is documented in [backend/API_CONTRACT.md](backend/API_CONTRACT.md). The Python dependency snapshot is in `backend/requirements-lock.txt`; the frontend snapshot is in `frontend/pnpm-lock.yaml`. Keep using `pnpm install --frozen-lockfile` to reproduce the verified frontend dependency graph.

Project source is MIT licensed. Dependencies retain their own licenses; see [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).

## Troubleshooting

- **The browser page is missing:** run `pnpm build` in `frontend/`, return to the repository root, and start the server with the virtual environment's Python. Open the displayed URL manually.
- **Port 8000 is already in use:** stop the other Easy Street backend with Ctrl+C, then start only one backend. A development Vite process on port 5173 can run beside it.
- **PowerShell says a script cannot run:** use the documented `.venv\Scripts\python.exe`, `npm.cmd`, and `pnpm.cmd` commands; activation is not required.
- **Frozen lockfile installation fails:** use pnpm 10 and the unmodified `package.json` and `pnpm-lock.yaml` from the same checkout. Do not discard the lockfile to hide a dependency mismatch.
- **Linux cannot create a virtual environment:** install your distribution's Python 3.12 venv support, then rerun the environment creation command.
- **The provider is unavailable:** configure your own backend key, check your provider account access and billing, then restart. The offline sample remains available.
- **Budget exhausted:** check Settings and uncertain reservations before raising the local limit. Changing the cap does not change provider-side billing controls.
- **Unreadable PDF:** use a text-based PDF, a smaller chapter, or a locally OCR-processed copy. Encrypted PDFs are rejected.
- **A section needs review:** open its source references, correct unsupported text, and keep manual edits. Regeneration saves a previous version and marks dependent material for review.
- **Cross-origin request blocked:** use `127.0.0.1:8000` in production or the documented Vite development origin. Do not disable origin protection to embed the app in another website.

Easy Street is a working product name; domain and trademark availability have not been verified.
