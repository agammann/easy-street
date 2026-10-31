# Easy Street

**Big ideas. Your own way.**

Turn reading you already have into an editable personal course. Upload a PDF, DOCX, or text file, inspect its extraction, choose your modules and assessments, approve the outline, and generate one module at a time.

![An open book becomes a road through colorful hills](frontend/public/learning-road.png)

Easy Street is free, MIT-licensed software that runs on your computer. **Bring your own OpenAI API key and pay OpenAI directly for live generation.** There is no bundled key, shared developer billing account, subscription, or required hosted service. The included offline demo needs no key.

## Features

- **1–6 modules**, with a proposed syllabus, course and module objectives, introductions, source-linked readings, notes, and announcements.
- **0–6 written assignments and 0–6 quizzes as course-wide totals**, with at most two of each per module. Assignments include rubrics; quizzes contain 1–5 questions with separate answers and explanations.
- Editable module titles, objectives, assessment placement, and source selection, with coverage and repetition warnings before approval.
- Source inspection, section editing/reordering/regeneration, version history and restore, course archive/unarchive, and JSON course import.
- Printable learner HTML, a separate answer key, and a structured JSON backup.
- Local PDF, DOCX, and UTF-8 TXT extraction; optional explicit local OCR for selected PDF pages.

Source checks and a separate model review can miss unsupported claims. Read the source and review generated content before relying on it or sharing it. Objectives, activities, schedules, and rubrics are proposals, not textbook policies or accreditation. See [verification results and limits](COMPLETION_REPORT.md).

## Download and start

Download **easy-street-1.0.1.zip** from the [latest release](https://github.com/agammann/easy-street/releases/latest), then extract the whole ZIP into a writable folder. This asset includes the built interface: **end users do not need Git, Node.js, or a frontend build**. GitHub's automatic source-code ZIP is a different download and still needs a build.

1. Install **Python 3.12** from [python.org](https://www.python.org/downloads/). Include the Python launcher on Windows.
2. Open the extracted `easy-street` folder. On Windows double-click **Easy Street.cmd**. On macOS open **Easy Street.command**, or use the terminal command below. On Linux use the terminal command.
3. The first run creates a private `.venv` environment and downloads pinned Python dependencies. This setup needs internet access; later starts reuse it.
4. The app opens at **http://127.0.0.1:8000**. Keep the terminal open while using it. Press **Ctrl+C** there to stop.

From the app folder, the equivalent commands are:

```powershell
# Windows PowerShell
py -3.12 launch.py
```

```sh
# macOS / Linux
python3.12 launch.py
```

If `python3.12` is unavailable but `python3 --version` reports 3.12, use `python3`. Open a new terminal after installing Python if its command is not found. No PowerShell activation script or execution-policy change is needed. The launcher supports `--no-browser` and `--setup-only`.

### Try a course without a key

1. Choose **Try the sample chapter**.
2. Inspect the passages, then **Looks good. Shape my course**.
3. Keep **Offline demo** selected, choose your counts, and **Preview my outline**.
4. Review module coverage and assessment placement. Approve the outline and review the **$0.00** estimate before generating.
5. Review the completed course, try **Show source**, edit a section, and export learner HTML or the answer key.

The demo uses prewritten content for the included original garden chapter. It demonstrates the workflow, not live model quality. Your own material can be uploaded and outlined locally without a key; provider generation needs your key.

### Configure your own key and budget

Stop the app and run this from its folder:

```powershell
# Windows
py -3.12 launch.py --configure
```

```sh
# macOS / Linux
python3.12 launch.py --configure
```

The terminal prompt hides the key as you type and saves it in the ignored `.env.local` file. Enter your own key and a cumulative local budget in USD; Enter keeps an existing value. Restart and check **Settings** for the configured-key indicator and allowance.

In Codex, its secure OpenAI key setup flow is also supported. Advanced users can configure `OPENAI_API_KEY` and `EASY_STREET_BUDGET_USD` in the backend environment or edit `.env.local` with a trusted editor. `.env.example` has no key; copy it only if `.env.local` does not already exist.

Never paste keys into chat, courses, the browser interface, issues, or source code. There is no browser key-entry form. Keys are not stored in SQLite, browser storage, or exports. Protect `.env.local` with your operating-system account and backup practices. The default allowance is **$1 per local database**, cumulative rather than per-course or daily.

## Planning and recovery

**Upload → Review extraction → Set options → Approve outline → Generate → Review/edit → Export.** Counts are course-wide totals. Each module supports at most two assignments and two quizzes, so higher totals may require more modules. Adjust their placement without changing the totals.

Each module uses at most **24,000 source characters and 512 evidence excerpts**. Longer source partitions are sampled across their span; omissions are reported before approval. Unselected material is not covered. You can adjust source selection and assessment placement before the first module is generated. After generation begins, those structural choices are locked; titles and objectives remain editable. Complete coverage of an arbitrary book is not promised.

Generation proceeds by module, persisting completed stages and caching outputs by source, settings, model, and prompt version. Section regeneration preserves unrelated manual edits. Changed learning content marks related assessments for review.

After a refresh or restart, select the course in **My courses** to recover its latest job. A safe interrupted job offers **Resume safely**, reusing completed stages. An **uncertain** job cannot automatically resume because repeating it could duplicate a paid request; its remaining reservation stays held. Check the provider dashboard before deliberately starting new work. Cancellation stops later work but may not stop or avoid charges for an in-flight request.

### Backups, versions, and archives

- Export course JSON, then use **Import JSON backup** in My courses to restore it as a new course. Import never overwrites another course and marks imported content for review. JSON includes answers, short evidence quotes, and locations for selected or cited passages; unused source locations, the original file, and complete extracted text are excluded. Reattaching the exact original restores its full extraction.
- Imported courses can be read, edited, and exported without their original. To inspect complete evidence or regenerate, use **Restore original source** and select the exact original file; its hash and extraction identity must match. OCR-derived sources also need the optional OCR tools, and recognition changes after a tool upgrade may prevent a match.
- For a completed imported or restored course, choose **Review outline**, approve the checkbox, then **Approve outline & return** before regenerating a section. For an unfinished course, choose **Continue remaining modules**, approve the checkbox, then **Review cost & continue**.
- To restore older work, choose **Version history**, select a version, then **Restore this version**. The current version is saved first, so restoration can be reversed.
- Archived courses stay on this device: choose **Archived**, then **Unarchive** to bring one back. Archiving does not erase data or release uncertain reservations.

Local state is in `data/` by default; `EASY_STREET_DATA_DIR` selects another location. For a complete workspace backup, stop the server and back up the entire data directory, including its database and originals. Course JSON is not a full workspace backup. Keep secrets separate from shared backups.

To upgrade, stop the old app, extract the new release into a new folder, and copy `data/` and your private `.env.local` into it. Keep the old folder until saved courses are verified. Do not copy `.venv`; the launcher creates a new one. Preserve custom data-directory configuration instead of copying data twice. Run only **one backend process per data directory**.

## Optional local OCR

Readable PDFs need no OCR. For scanned or poorly extracted pages, the preview shows pages that may need it. OCR is optional, English-only, explicitly selected, and local: **no paid vision service is used**.

Install Tesseract with English language data using its [installation documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html), then install the optional renderer:

```powershell
# Windows, after Tesseract is installed and on PATH
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-ocr.txt
```

```sh
# macOS, with Homebrew already installed
brew install tesseract
.venv/bin/python -m pip install -r backend/requirements-ocr.txt

# Ubuntu / Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng
.venv/bin/python -m pip install -r backend/requirements-ocr.txt
```

Restart the app, choose up to five pages in the preview, and run local OCR. Changed page selections or recognition output create a separate extraction; identical selections and output reuse the saved extraction. Keep prior page selections to retain their recognized text. Existing course evidence is preserved. When reopening an older source, select its PDF again to OCR it. Review recognized text carefully; formulas, handwriting, tables, and complex layouts remain unreliable.

## Privacy and spending

Original files, extraction, outlines, courses, versions, jobs, and usage stay local. Approving generation sends selected excerpts and course instructions to OpenAI; a separate support review receives the relevant source and generated content. Requests use `store=False`, and provider processing remains subject to its policies. Generation has no web search, outside retrieval, or execution tools. Uploaded text is treated as untrusted data.

The app checks counts, source identifiers, and exact quotations, then asks the provider to assess support. A valid quotation does not prove that every claim follows from it. Missing support and detected conflicts are flagged, but the reviewer is fallible. Human review remains necessary.

Default model: `gpt-4.1-mini`. Pricing checked October 15, 2026: **$0.40/million input tokens, $0.10/million cached input tokens, $1.60/million output tokens**. See [official pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini). Estimates include generation and verification and conservatively use the full input rate. Recorded costs use provider-reported tokens and are estimates, not invoices.

The app reserves estimated costs and checks the allowance before each call. Automatic SDK retries are disabled. **Local allowances are not provider-enforced billing caps.** The server binds to localhost and checks Host/Origin requests. This is a personal workspace without multi-user authentication; do not expose it to a public network.

## Build from source

Developers need Git, Python 3.12, Node.js 22.12 or newer, and pnpm 10. Release ZIP users do not need Node.js.

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

Use Python 3.12 for `python3`. Open http://127.0.0.1:8000 manually for `start.py`. For development, stop it, run `.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`, and run `pnpm dev` in `frontend/` in a second terminal. On Windows use `.\.venv\Scripts\python.exe` and `pnpm.cmd`. Open http://127.0.0.1:5173. Vite proxies the API to the one Python backend. Rebuild before returning to production startup.

## Tests

```powershell
# Windows, from the repository root
.\.venv\Scripts\python.exe -m pytest backend/tests tests/integration
Set-Location frontend
pnpm.cmd test
pnpm.cmd build
Set-Location ..
.\.venv\Scripts\python.exe scripts/smoke_startup.py
```

On macOS/Linux use `.venv/bin/python`, `cd`, and `pnpm` in equivalent commands. Stop the backend before the startup smoke test; it requires port 8000. It uses an isolated temporary copy without keys or saved data and checks assets, extraction, offline generation, exports, and restart persistence. These tests make no paid calls. The real OCR test runs when optional tools are available, otherwise it is explicitly skipped.

[GitHub Actions](https://github.com/agammann/easy-street/actions) runs Ubuntu, Apple Silicon macOS 15, and Intel macOS 15 separately. It packages the download and checks fresh installation from the ZIP without building the frontend. Ubuntu installs optional tools for a real OCR test. Run it from any computer using **Actions → Check Easy Street → Run workflow**.

See [COMPLETION_REPORT.md](COMPLETION_REPORT.md) for actual results. Hosted macOS checks do not establish interactive Safari or desktop-installer behavior. API details are in [backend/API_CONTRACT.md](backend/API_CONTRACT.md).

## Troubleshooting and limits

- **Missing Python:** install Python 3.12 and reopen the terminal. Linux may also need its Python venv package.
- **Missing frontend:** download the release asset `easy-street-1.0.1.zip`, rather than GitHub's automatic source ZIP, or follow source build instructions.
- **Port 8000 occupied:** stop the other backend with Ctrl+C; use only one server per data directory.
- **Dependency setup failed:** check internet access and Python version, then rerun. Keep lockfiles intact.
- **No configured key:** run the private configuration command, check provider access/billing, and restart. Offline demo remains available.
- **Budget exhausted:** inspect Settings and uncertain reservations before increasing the limit.
- **Unreadable source:** use a clearer file or explicit local OCR. Encrypted PDFs, legacy `.doc`, macros, and embedded DOCX objects are unsupported.
- **Review needed:** inspect source evidence and correct unsupported wording. A different source file needs a new course.
- **Cross-origin blocked:** use documented localhost URLs and ports; do not disable protections for embedding elsewhere.

Limits: **15 MiB uploads, 100 PDF pages, 250,000 extracted characters**, additional DOCX archive/XML expansion limits, and five selected OCR pages per upload. Hosted accounts, LMS integration, automatic grading, additional providers, and unrestricted full-book generation are outside this release.

Use material you have permission to process. Learner HTML is the sharing format when answers must remain separate; JSON and answer keys include answers. Exports omit complete source documents but may include short quotations.

Project source is MIT licensed. Dependencies keep their own licenses; see [dependency notes](docs/DEPENDENCIES.md) and [built-interface notices](THIRD_PARTY_NOTICES.txt). Easy Street is a working product name; domain and trademark availability have not been verified.
