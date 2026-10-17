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
6. Test both adapters and hosted boundaries with mocks, then inspect desktop/mobile workflows. After explicit approval and secure Nebius setup, check the authenticated model catalog and run one small live course; record usage, latency, quotations, review findings and measured cost separately from mocks.
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

No prior OpenAI development cap is reused for Nebius. The owner approved **up to $1 total for a small Nebius live test** on October 16; the separate masked key prompt was also approved. Fly hosting and **$15 total through December 15** are now approved ($8 hosting, $3 aggregate inference including actual development charges, $4 contingency). Deployment is approved conditional on final checks and a passing live Nebius test; runtime generation remains at zero until those conditions pass. Credentials, new account agreements, and payment setup remain under the owner's private control. Free Better Stack email monitoring and labeled test alerts to the verified account email are approved, using the read-only operator status endpoint; configuration and delivery remain unverified. All routine tests use mocks. Promotional credit is counted as **$0 guaranteed** until actual issuance, expiry and applicable terms are verified. Pending: secure credentials and real-call verification, final deployment checks, actual monitoring configuration/notification receipt, and separate merge, release, video-publication, agreement, and submission approvals. Branch publication and draft PR creation are approved and complete.
