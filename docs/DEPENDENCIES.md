# Dependency license review

Reviewed October 15, 2026 against the installed packages used for the release checks. Easy Street's original source is released under the repository's MIT license. Third-party packages retain their own licenses and copyright notices; the project MIT license does not replace them.

The review used Python distribution metadata and shipped license files, the exact backend lock, and `pnpm licenses list --json` for the active frontend dependency graph. It covered 31 installed Python dependencies and 129 installed JavaScript package versions across 126 package names on Windows. Old packages left in the package-manager cache were excluded from the active graph. Optional binaries for other platforms were not individually downloaded for this review.

Dependency source, virtual environments, package-manager caches, and the frontend build are excluded from this source repository. When distributing a prebuilt application or vendoring packages, retain the corresponding dependency licenses and notices alongside that distribution.

## Direct backend dependencies

| Package | Tested version | Declared license |
| --- | --- | --- |
| FastAPI | 0.143.2 | MIT |
| Uvicorn | 0.54.0 | BSD-3-Clause |
| python-multipart | 0.0.32 | Apache-2.0 |
| pypdf | 6.20.1 | BSD-3-Clause |
| OpenAI Python SDK | 2.54.0 | Apache-2.0 |
| Pydantic | 2.14.1 | MIT |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| HTTPX | 0.28.1 | BSD-3-Clause |
| pytest | 9.1.1 | MIT |

Exact transitive versions are recorded in [backend/requirements-lock.txt](../backend/requirements-lock.txt).

## Optional local OCR

DOCX extraction uses Python's standard ZIP and XML libraries and adds no package dependency. Local PDF OCR is an optional installation; ordinary PDF/TXT/DOCX extraction and the offline demo do not require it.

| Component | Version | Declared license |
| --- | --- | --- |
| pypdfium2 | 5.14.0, pinned in `backend/requirements-ocr.txt` | Apache-2.0 OR BSD-3-Clause |
| PDFium bundled by the pypdfium2 wheel | Determined by the wheel | BSD-style license, plus notices for bundled dependencies |
| Tesseract and English language data | Installed separately using the operating system's package manager | Tesseract: Apache-2.0; language data and binary dependencies retain their own notices |

The [pypdfium2 licensing documentation](https://pypdfium2.readthedocs.io/en/stable/readme.html#licensing) identifies the wrapper's dual license and requires PDFium and bundled dependency notices with binary distributions. The [Tesseract project](https://github.com/tesseract-ocr/tesseract) documents its Apache-2.0 license and local command-line usage. Easy Street invokes the installed Tesseract executable and does not bundle it. Review the licenses of the actual operating-system package or installer before redistributing a binary application; the base dependency graph review above does not cover arbitrary third-party Tesseract installers.

## Frontend dependencies

| Package | Tested version | Declared license |
| --- | --- | --- |
| React | 19.3.1 | MIT |
| React DOM | 19.3.1 | MIT |
| Lucide React | 0.468.0 | ISC; its license also preserves Feather portions under MIT |
| TypeScript | 5.9.3 | Apache-2.0 |
| Vite | 8.3.4 | MIT |
| Vitest | 5.0.4 | MIT |
| Vite React plugin | 6.1.2 | MIT |
| Testing Library jest-dom | 6.9.1 | MIT |
| Testing Library React | 16.3.3 | MIT |
| Testing Library user-event | 14.6.8 | MIT |
| React and React DOM type definitions | 19.3.0 | MIT |
| jsdom | 25.0.1 | MIT |

Exact versions and integrity values are recorded in [frontend/pnpm-lock.yaml](../frontend/pnpm-lock.yaml). The active frontend graph contains MIT, MIT-0, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, and MPL-2.0 packages. No package in that reviewed graph had missing license metadata.

## Transitive licenses that need separate notices

- **certifi 2026.7.22:** MPL-2.0 for the Mozilla-derived CA certificate bundle. Its packaged license identifies the upstream certificate data and the MPL terms.
- **tqdm 4.70.1:** MPL-2.0 and MIT. Its packaged license identifies the respective contributions and retains both notices.
- **lightningcss 1.33.0 and its Windows native binary:** MPL-2.0. These are frontend build-tool dependencies; their license remains separate from Easy Street's source license.
- **typing_extensions 4.16.0:** PSF-2.0, with the Python license history and notices included in its distribution.
- **packaging 26.3:** Apache-2.0 OR BSD-2-Clause. **sniffio 1.3.1:** MIT OR Apache-2.0.
- Other reviewed Python dependencies declare MIT, Apache-2.0, BSD-2-Clause, or BSD-3-Clause. The application does not modify these third-party packages.

The reviewed graphs did not identify GPL or AGPL packages. This is a release-specific metadata and notice review; dependency upgrades require a new check. License review and vulnerability checks are separate activities; see the completion report for the commands and results of release testing.
