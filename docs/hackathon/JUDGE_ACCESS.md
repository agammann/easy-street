# Judging access preparation

This public file contains no credentials. **No hosted URL or testing-access arrangement is active yet.** Fly hosting and $15 total through December 15 are approved ($8 hosting, $3 aggregate inference including development, $4 contingency), with deployment conditional on final checks and a passing live Nebius test. Credentials, new account agreements, and payment setup stay under the owner's private control; runtime generation remains zero until the conditions pass. Free Better Stack email monitoring and labeled test alerts to the verified account email are approved, using the read-only operator status endpoint, but configuration and delivery are unverified. Branch publication and draft PR creation are approved and complete; merge, a new release, video publication, and entry submission remain unapproved. Fill the private testing fields only after the deployed workflow is verified.

## Intended access

Judges receive an HTTPS application URL and a private judge password in Devpost's testing instructions. It is an application-access password, separate from the operator token and Nebius API key. The host stores its PBKDF2 password hash; the operator-funded Nebius key stays in the host's secret environment. Judges do not provide their own API key or pay for testing.

After login, each browser receives an opaque HttpOnly session cookie and its own temporary documents, courses, results, jobs, database, and cache. Two browsers using the same judge password must still receive independent visitor workspaces. Use a fresh browser context to test this boundary. Sharing the access password never shares a provider credential or another visitor's content.

The intended availability period runs through **December 15, 2026, noon PST**. The prepared expiry is midnight PST at the end of December 15 (`2026-12-16T08:00:00+00:00`). The [rules](https://nebiusglobalaihackathon.devpost.com/rules) require free judging access and allow private sites when credentials are supplied. Temporary workspaces, bounded per-call tasks, and an emergency operator allowance must not become a routine barrier to legitimate judging. Monitor headroom and provide operator assistance if capacity or the temporary-session allowance is exhausted.

The operator prepares access values with [scripts/configure_judging.py](../../scripts/configure_judging.py), using `.\.venv\Scripts\python.exe scripts/configure_judging.py` on Windows or `.venv/bin/python scripts/configure_judging.py` on macOS/Linux. Hidden prompts create a PBKDF2 hash and random operator token in ignored `deploy/.env.judging.local`; no provider key is requested, no credential is printed, and the initial generation allowance stays zero. Enter the dedicated Nebius key separately through the owner-controlled private host setup. Enable only the remaining approved inference amount after the live-test/final-check conditions pass. Keep the plaintext access code only in the approved private instructions/password manager.

## Testing steps to put in the private entry

1. Open the approved HTTPS URL in a fresh browser window and sign in with the credential supplied privately. No registration, payment, or provider account is required.
2. Choose **Generate sample with Nebius** for the one-click original garden chapter workflow. Its disclosure identifies the included licensed source and provider; preset small-course settings skip the manual outline steps in step 3. A funded operator configuration is required; an unavailable provider is not replaced with mock generation.
3. For the manual workflow, choose **Try the sample chapter** or upload a PDF, DOCX, or TXT chapter you may process. Hosted upload size is 5 MiB; readable text is required because the judging image does not include optional local OCR tools. Review extracted passages, configure modules/assignments/quizzes/questions, and approve the outline/source disclosure. Hosted counts are bounded to three modules, three assignments, and three quizzes. Regular local installations retain the broader released limits.
4. Generate using Nebius Token Factory. The configured NVIDIA model is `nvidia/nemotron-3-super-120b-a12b`; final instructions must match the actual tested deployment. Describe the measured wait time after the approved live test. A cached result must be labeled accordingly.
5. Open source evidence beside a learning note or quiz. Compare exact quotations and source locations, inspect review warnings, and edit the result. Automated support review is fallible; missing evidence must remain visible.
6. Regenerate a section, export learner HTML, and inspect the separate answer key if useful. A JSON backup contains answers and selected quotations; avoid sharing it as a learner-only handout.
7. Delete the temporary workspace when finished. The prepared active-workspace retention period is 24 hours; active work may delay physical removal. The proposed Fly volume also retains daily snapshots for five days, so application deletion does not instantly erase backup copies. Tell judges the final host's verified cleanup and backup retention before submission; no host policy is active yet.
8. If access, capacity, or generation fails, use the privately supplied monitored owner contact. A spending cutoff needs operator intervention. Do not ask judges to top up credits, disclose their own key, or solve an operator billing issue.

## Private fields to complete outside Git

| Field | Current state |
| --- | --- |
| Application URL and deployed revision | Conditional deployment approved; final checks, passing live test, secure setup, and actual deployment pending |
| Judge password | Not recorded here; private testing field only |
| Monitored access-help route | Owner must approve and confirm |
| Verified average/maximum small-run wait | Pending approved live test |
| Working period and operator coverage | $15 through December 15 approved; actual host availability and monitoring verification pending |
| Cleanup behavior observed | Pending acceptance test |
| Last fresh-session verification | Not performed against a deployed service |

## Acceptance before offering access

- [ ] Open from an unauthenticated desktop browser; protected API calls cannot read documents or spend credits.
- [ ] Login and complete the real Nebius sample path with no BYO credentials.
- [ ] Upload a different permitted chapter and exercise outline, configurable counts, evidence, editing, regeneration, and exports.
- [ ] Repeat in a separate browser session. Attempts to retrieve the first session's IDs, jobs, originals, or exports fail.
- [ ] Verify duplicate clicks do not repeat a paid request and a cached repeat makes no provider call.
- [ ] Complete the mobile workflow with readable evidence and no hidden primary controls.
- [ ] Delete a workspace; confirm server-side records/files become unavailable while non-content shared accounting remains intact.
- [ ] Observe expiry cleanup and restart behavior on the approved host's persistent disk.
- [ ] Exercise wrong login, missing credentials, unavailable provider, malformed output, quota exhaustion, and the global cutoff using mocks/test configuration.
- [ ] Confirm low-balance and outage/recovery notifications actually reach the approved destination.
- [ ] Verify final judge instructions, private credentials, recovery contact, and the working period with the owner before submission.

The video and source are complementary evidence. They do not replace a functioning application or test build. If a legitimate judge encounters a restriction, the named operator must resolve it promptly and record the interruption honestly.
