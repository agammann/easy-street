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
6. Test both adapters and hosted boundaries with mocks, then inspect desktop/mobile workflows. Two local approved live runs and one hosted run have checked the authenticated model catalog and actual generation/support review, including revised prompt v2.1 and cache identity. Keep their measured results separate from mocks. Seven edits were saved in the second hosted cached copy while retaining raw evidence. Owner content review and any further correction of coverage/precision gaps remain required before accepting demonstration content.
7. Prepare setup/architecture/license documentation, contest change history, a sub-three-minute video script, a Devpost draft and private judge instructions. Freeze and publish only after approval; deploy and verify in a fresh browser only after host, budget and deployment approval.

## Eligibility and release gates

Sources: [official rules](https://nebiusglobalaihackathon.devpost.com/rules), [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs).

- Target track: **Best Apps and Agents**. Runtime generation must use NVIDIA Nemotron through Nebius Token Factory; switching a label or using another host's model API is insufficient.
- Deadline: **October 30, 2026, 10:00 a.m. America/Los_Angeles**. Judging ends **December 15, 2026, noon America/Los_Angeles**. Recheck for rule updates before submission.
- Existing repository reuse is allowed. The original Git history begins October 15, inside the contest window; record the actual adaptation delta rather than claiming a pre-contest origin.
- Submission needs a working demo/test build, public open-source source and setup directions, English description, track, actual tool feedback, and a public YouTube video under three minutes.
- Private judging access is allowed with credentials in testing instructions. Judges must receive free access through judging. Ordinary bounded tasks and private access protect the shared account; emergency cutoff exhaustion interrupts judging and requires operator intervention.
- Personal eligibility, residence, conflicts of interest, ownership and any agreements require the owner's confirmation.
- Publication, repository visibility changes, video upload, agreements and final submission require approval.

## Current implementation and remaining gates

The [approved Fly service](https://easy-street-agammann-2026.fly.dev) is deployed from runtime `0c010c0`, on the same 512 MiB machine and 1 GiB volume. The replacement clarifies active-workspace versus backup retention and includes the validated Fly path correction. Real hosted login/sample/evidence/exports, two-session HTTP isolation/deletion, restart persistence, zero-cost cached reuse, saved editor changes, and scheduled cleanup of a deliberately expired owned fixture were exercised on `0e0c17d`. The expiry test did not wait a real 24 hours. Three actual development/hosted jobs still total $0.0115005 estimated from reported tokens; replacement acceptance made no new provider call. See [VERIFICATION.md](VERIFICATION.md) for exact usage, current revision-pinned CI, image identity, and replacement checks.

The owner approved Fly and **$15 total through December 15** ($8 hosting, $3 aggregate inference including development, $4 contingency). The funded hosted allowance deducts prior development spending; it does not purchase credits, establish an invoice, or impose a platform-wide cap. Promotional-credit expiry is not guaranteed. An emergency cutoff interrupts judging and requires operator intervention.

Two approved free Better Stack monitors are configured and Up: public readiness and authenticated operator attention, checked every three minutes with SSL verification, redirects disabled, and email-only notifications. Labeled incident 1033213383 was resolved, and the owner confirmed receiving both incident-started and resolved emails through the normal free route. Adding a separate outgoing-email integration encountered a Free-plan paywall; no upgrade or external email integration was used. The team notification recipient was verified to be only the owner. Other new agreements remain owner-controlled.

Current runtime [CI run 38999513875](https://github.com/agammann/easy-street/actions/runs/38999513875) is fully green at `0c010c0`, including privacy wording and the committed, validated Fly Dockerfile-path correction. New 512 MiB/0.5 CPU local Docker acceptance passed with zero provider calls. Later documentation is separate from that archive. Branch publication/draft PR and deployment are approved and complete. Pending: owner content review of raw findings and the edited copy; final private judge code/contact placement; ongoing budget/expiry/capacity checks; recording and video publication; personal attestations; final Devpost submission; and separate merge/new-release approvals. Routine provider tests remain mocked except for the explicitly measured real calls.
