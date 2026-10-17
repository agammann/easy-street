# Hackathon eligibility and release gates

Checked October 16, 2026 against the [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules) and [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs). Recheck both immediately before submitting. This checklist records preparation; it does not attest personal eligibility or accept an agreement.

## Dates and requirements

| Item | Verified requirement | Easy Street evidence or remaining gate |
| --- | --- | --- |
| Submission | August 26, 2026, 9 a.m. Pacific through **October 30, 2026, 10 a.m. PDT** | Branch publication/draft PR approved and complete; final entry and video still require approval before the deadline. |
| Judging | December 1, 9 a.m. through **December 15, 2026, noon PST** | Approved host, funding, access, and tested alert delivery remain deployment gates. |
| Track | Best Apps and Agents | Nemotron must perform useful course work through Token Factory. A mocked response or provider selector alone is insufficient. |
| Platform | Nebius runtime use and an NVIDIA open model | The FAQ permits other hosting for the web application. The authenticated catalog and two approved live generation/support-review runs passed, including revised prompt v2.1. Citation coverage and precision still need owner review and correction. See [verification](VERIFICATION.md). |
| Existing work | Significant updates during the contest window | [CONTEST_CHANGES.md](CONTEST_CHANGES.md) distinguishes the released baseline from adaptation changes. |
| Source | Public open-source repository, setup, necessary assets | MIT [hackathon branch](https://github.com/agammann/easy-street/tree/hackathon/nebius-nemotron-2026) is public with [draft PR #1](https://github.com/agammann/easy-street/pull/1). Packaging correction [1f75aa9](https://github.com/agammann/easy-street/commit/1f75aa907e647b06bb416b4ae13536281842aaf9) passed [all three CI runners](https://github.com/agammann/easy-street/actions/runs/38995934439); later changes require their own checks. Not merged/released. |
| Entry | English description, track, tool feedback, working demo/test build | [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md); final deployed/video URLs and owner content acceptance pending; both real-call results are recorded in [verification](VERIFICATION.md). |
| Video | Public YouTube demonstration under three minutes | [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md); record real functioning software after validation. |
| Testing | Free judge access until judging ends; private sites supply credentials | Add credentials only to the private testing field. No provider key is a judge credential. |

The four equally weighted criteria are implementation, design, impact, and idea. Demonstrate a useful workflow, readable evidence review, a specific audience, and substantive Nemotron integration. See the [judging section of the rules](https://nebiusglobalaihackathon.devpost.com/rules).

## Personal confirmations before entry

The owner must confirm age of majority, residence eligibility, conflicts and employment/household exclusions, rights to all submitted material, authorized team representation if applicable, and any disqualifying preferential support. These facts cannot be inferred from a GitHub profile. Read the full eligibility, ownership, financial-support, release, and publicity provisions in the [rules](https://nebiusglobalaihackathon.devpost.com/rules) before accepting them. No checkbox or agreement has been accepted by preparing this branch.

## Credits are not guaranteed judging funding

| Offer | Published validity | Operational consequence |
| --- | --- | --- |
| New-account $1 trial | 30 days from signup | A hypothetical October 16 signup expires around November 15, before judging. |
| Builder Program $25 | 90 days from issuance | A hypothetical October 16 issue reaches January 14, 2027; an August 26 issue reaches November 24. Actual account timestamps govern. |
| Hackathon direct $25 code | No exact expiry found in the public offer | Obtain the actual issuance/redemption/expiration terms before counting it. |

Sources: [Token Factory billing](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new), [Builder terms, sections C and H](https://nebius.com/builders-terms-and-conditions), [hackathon resources](https://nebiusglobalaihackathon.devpost.com/resources). Builder credits are restricted to prototyping and experimentation; they are not a production entitlement. Offers can change. No promotional credit is counted as guaranteed judging funding here. Budget conservatively as if credits contribute $0 until verified.

Token Factory billing describes automatic card charging at the configured threshold or for a negative balance at month start. An application allowance does not impose a provider billing cap. A paid fallback needs explicit approval. The current [Token Factory legal notice](https://docs.tokenfactory.nebius.com/legal/terms-of-service) points new/non-reserve customers to the [Nebius Services Agreement](https://docs.nebius.com/legal/agreement); do not assume legacy terms apply.

## Release decision

As of October 16, the owner approved up to $1 total for a small Nebius live test and opening masked local key setup. The development key was configured privately, the authenticated model catalog was checked, and the first real sample completed: 5,984 input tokens, 1,397 output tokens, 8.62 seconds, and $0.0030525 estimated from reported tokens. Its ten sections had zero automatic flags, but a separate content inspection found an introduction citing only a title and an unsupported assurance. Revised prompt v2.1 then completed another ten-section run with exact quotations in 10.50 seconds. Across both runs, reported usage totals 14,063 input / 3,275 output tokens and $0.0071664 estimated cost, without reserves or uncertain calls. The revised introduction now cites substantive material and drops the absorption guarantee, but citation-coverage and approximation gaps remain. Live integration is verified; owner review and manual correction remain required. The owner confirmed Fly hosting and $15 total through December 15 ($8 hosting, $3 aggregate inference including development, $4 contingency), with deployment conditional on final checks and a passing live Nebius test. The prepared judging allowance remains zero until those conditions pass. Free Better Stack email monitoring and labeled test alerts to the verified account email are approved, but the specific free-account terms are approved and signup reached email verification; no monitor is configured and delivery is untested. Credentials, new account agreements, and payment setup remain owner-controlled. Branch publication and draft PR creation are approved and complete. Merge, a new release, video publication, and entry submission remain unapproved.

- [x] Both providers pass routine mocked regressions, including evidence and cost failures; see [verification](VERIFICATION.md).
- [x] First approved Nebius test records authenticated model, tokens, cost, latency, exact quotations, and the content-review defect; see [verification](VERIFICATION.md).
- [x] Revised prompt v2.1 and its cache identity completed a fresh live run; the original run evidence remained unchanged.
- [ ] The owner reviews and corrects remaining citation-coverage and approximation gaps before accepting demonstration content.
- [ ] A fresh deployed desktop and mobile session completes real sample, upload, evidence, export, and deletion. Local mock-backed checks do not satisfy this deployed gate.
- [x] Local automated/container checks reject a second visitor's access to the first visitor's resources; repeat on the approved public host.
- [x] Free email monitoring/test alerts to the verified account email are approved; actual configuration and delivery remain separate gates.
- [x] Fly hosting and the $15 total budget are approved; deployment approval is conditional on final checks and a passing live Nebius test.
- [ ] Final private judge access and production-secret/account setup are complete. The development Nebius key alone does not complete deployment setup.
- [ ] Actual deployment and alert delivery are verified; retention cleanup is observed.
- [ ] Credits and paid fallback cover the period through December 15; cutoff recovery has an owner.
- [x] Publish the approved source branch/revision and open its draft PR; see [verification](VERIFICATION.md) for the packaging correction and revision-specific checks.
- [ ] Publish the video only after recording, review, and approval; merge/new release remain separate approvals.
- [ ] The owner confirms attestations and explicitly authorizes terms acceptance and final submission.

An emergency spending cutoff interrupts live judging. It requires operator intervention to replenish approved funds, revise the approved allowance, or repair abuse. A static recording and cached result do not substitute for an available working judging deployment.
