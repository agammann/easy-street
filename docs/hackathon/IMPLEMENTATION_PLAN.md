# Nebius hackathon implementation plan

Reviewed October 16, 2026. Branch: `hackathon/nebius-nemotron-2026`.
Baseline: `cc00965b3a667339584742c429d4b212301791dd` (published v1.0.0).
Initial Git tree was clean; no unrelated modifications were present.
Baseline checks: 136 backend tests passed, one optional OCR test skipped; 35 frontend tests passed.

## Architecture and bounded changes

Reuse the React/TypeScript interface, FastAPI routes, SQLite stores, evidence catalog, document extraction, source approval, module checkpoints, cost reservations and printable exports. Do not replace this application.

1. Add a Nebius Token Factory Chat Completions adapter for a verified NVIDIA Nemotron model. Select the provider per course, preserve OpenAI and its existing cache identity, and retain exact quotations, separate support review, count validation and explicit uncertainty. Disable automatic retries, including after ambiguous paid outcomes.
2. Add an independent judging ASGI entry point. Each authenticated browser receives its own temporary directory, SQLite database and cache. A shared persisted operator ledger limits all Nebius calls, global concurrency and spending. Local installs retain their own keys and existing localhost guards.
3. Provide private judging access with server-side credentials, an opaque HttpOnly session cookie, strict origin checks, rate limits, bounded uploads/generation, temporary retention and deletion. Never put the Nebius API key in browser code, errors, exports or logs. Judge credentials belong only in private testing instructions.
4. Extend the current interface with provider-specific disclosure, a genuine Nebius sample workflow, hosted privacy/retention information, login and deletion controls. Keep normal uploads, configurable modules/assessments, evidence inspection, editing and exports.
5. Prepare a one-instance container deployment, persistent accounting, liveness/readiness checks, low-balance status and a tested monitoring runbook. No services, agreements, financial commitments or monitoring are activated without approval.
6. Test both adapters and hosted boundaries with mocks, then inspect desktop/mobile workflows. Two approved live runs have checked the authenticated model catalog and actual generation/support review, including revised prompt v2.1 and cache identity. Keep their measured results separate from mocks. Owner content review and manual correction of remaining coverage/precision gaps are required before accepting demonstration content or deploying.
7. Prepare setup/architecture/license documentation, contest change history, a sub-three-minute video script, a Devpost draft and private judge instructions. Freeze and publish only after approval; deploy and verify in a fresh browser only after host, budget and deployment approval.

## Eligibility and release gates

Sources: [official rules](https://nebiusglobalaihackathon.devpost.com/rules), [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs).

- Target track: **Best Apps and Agents**. Runtime generation must use NVIDIA Nemotron through Nebius Token Factory; switching a label or using another host's model API is insufficient.
- Deadline: **October 30, 2026, 10:00 a.m. America/Los_Angeles**. Judging ends **December 15, 2026, noon America/Los_Angeles**. Recheck for rule updates before submission.
- Existing repository reuse is allowed. The original Git history begins October 15, inside the contest window; record the actual adaptation delta rather than claiming a pre-contest origin.
- Submission needs a working demo/test build, public open-source source and setup directions, English description, track, actual tool feedback, and a public YouTube video under three minutes.
- Private judging access is allowed with credentials in testing instructions. Judges must receive free access through judging. Ordinary bounded tasks and private access protect the shared account; emergency cutoff exhaustion interrupts judging and requires operator intervention.
- Personal eligibility, residence, conflicts of interest, ownership and any agreements remain user attestations, not agent-certified facts.
- Publication, repository visibility changes, video upload, agreements and final submission require approval.

## Approval-dependent work

No prior OpenAI development cap is reused for Nebius. The owner approved **up to $1 total for small Nebius live acceptance** on October 16; the masked development-key setup is complete. The authenticated catalog and two real generation/review runs passed, including revised prompt v2.1. Their aggregate estimated cost is $0.0071664 with no reservation or uncertain call. A separate inspection caught support issues despite zero automatic flags; the second introduction improved, but citation coverage and approximation gaps remain. Owner content review and manual correction are pending. See [VERIFICATION.md](VERIFICATION.md) for per-run usage and evidence; live integration success is not deployment acceptance. Fly hosting and **$15 total through December 15** are now approved ($8 hosting, $3 aggregate inference including actual development charges, $4 contingency). Deployment is approved conditional on final checks and a passing live Nebius test; the prepared judging allowance remains zero until those conditions pass. Credentials, new account agreements, and payment setup remain under the owner's private control. Free Better Stack email monitoring and labeled test alerts to the verified account email are approved, using the read-only operator status endpoint; the specific free-account Terms/Privacy and sign-in email are approved, and signup reached a verification-link email. Email verification, monitor configuration, and notification delivery remain pending; other new agreements still need owner approval. Routine provider tests use mocks; the explicitly identified live result is separate. Promotional credit is counted as **$0 guaranteed** until actual issuance, expiry and applicable terms are verified. Fly CLI authentication and strict deployment-config validation passed without provisioning paid resources. Pending: owner content review/correction, final production-secret and deployment checks, actual monitoring configuration/notification receipt, and separate merge, release, video-publication, agreement, and submission approvals. See [VERIFICATION.md](VERIFICATION.md) for current revision-specific tests rather than treating an earlier green revision as proof of later edits. Branch publication and draft PR creation are approved and complete.
