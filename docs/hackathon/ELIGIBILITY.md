# Hackathon eligibility and release gates

Checked October 16, 2026 against the [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules) and [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs). Recheck both immediately before submitting. This checklist records preparation; it does not attest personal eligibility or accept an agreement.

## Dates and requirements

| Item | Verified requirement | Easy Street evidence or remaining gate |
| --- | --- | --- |
| Submission | August 26, 2026, 9 a.m. Pacific through **October 30, 2026, 10 a.m. PDT** | Branch publication/draft PR approved and complete; final entry and video still require approval before the deadline. |
| Judging | December 1, 9 a.m. through **December 15, 2026, noon PST** | Fly is deployed with approved funding and active monitors; both incident/recovery emails were received. Private judge-code placement and continued operation through judging remain gates. |
| Track | Best Apps and Agents | Nemotron must perform useful course work through Token Factory. A mocked response or provider selector alone is insufficient. |
| Platform | Nebius runtime use and an NVIDIA open model | The FAQ permits other hosting for the web application. The authenticated catalog, two local live runs, and the funded hosted Nebius sample passed technical checks, including revised prompt v2.1. Citation coverage and precision still need owner review and correction. See [verification](VERIFICATION.md). |
| Existing work | Significant updates during the contest window | [CONTEST_CHANGES.md](CONTEST_CHANGES.md) distinguishes the released baseline from adaptation changes. |
| Source | Public open-source repository, setup, necessary assets | MIT [hackathon branch](https://github.com/agammann/easy-street/tree/hackathon/nebius-nemotron-2026) is public with [draft PR #1](https://github.com/agammann/easy-street/pull/1). Deployed runtime source [0c010c0](https://github.com/agammann/easy-street/commit/0c010c00c160e1cb47c60eea7f758050c23a3831) passed [all three CI runners](https://github.com/agammann/easy-street/actions/runs/38999513875), including Python-only ZIP installation. Privacy wording and the validated Fly config-path correction are included; paid-generation evidence remains pinned to the preceding runtime. See [verification](VERIFICATION.md). Not merged/released. |
| Entry | English description, track, tool feedback, working demo/test build | [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md); [deployed URL](https://easy-street-agammann-2026.fly.dev) is active; video and owner content acceptance remain pending. Three real-call results are recorded in [verification](VERIFICATION.md). |
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

The owner approved Fly hosting and $15 total through December 15 ($8 hosting, $3 aggregate inference including development, $4 contingency). The service is now deployed at **[easy-street-agammann-2026.fly.dev](https://easy-street-agammann-2026.fly.dev)** with runtime source `0c010c0`, on the same 512 MiB machine and 1 GiB volume. Initial zero-budget session-isolation/deletion checks, a funded real sample, restart/source/course persistence, cache reuse, three exports, mobile evidence review, and seven editor saves were exercised on `0e0c17d`. The privacy/configuration replacement passed new CI and local bounded-container acceptance without another provider call. See [verification](VERIFICATION.md) for exact scope and replacement checks.

Three real local/hosted jobs used 20,932 input / 5,801 output tokens, estimated at $0.0115005, with no reservations or uncertain calls. The raw hosted course is `needs_review`; separate inspection found further support gaps. Seven corrections were saved in the second cached copy while leaving the first raw result untouched; review/dependency flags and owner content review remain open.

Two approved free Better Stack monitors are Up, checking availability and protected operator attention every three minutes with SSL verification, redirects off, and email-only notifications. A labeled test incident resolved, and the owner confirmed receiving both incident-started and resolved emails through the normal free route. No paid upgrade or external outgoing-email integration was used. The specific monitoring account terms/privacy were approved; other new agreements still need owner authorization. No personal email, judge code, operator token, or provider key belongs in this checklist.

- [x] Both providers pass routine mocked regressions and final runtime CI; see [verification](VERIFICATION.md).
- [x] Three approved real sample jobs record authenticated model, tokens, estimated cost, timing, quotations, and review limitations.
- [x] Revised prompt v2.1 completed a fresh local run; original first-run evidence was preserved.
- [x] Actual hosted desktop/mobile sample/evidence/export and hosted HTTP isolation/deletion checks passed within the recorded scope.
- [x] Hosted source/course/cookie persistence and zero-cost cached reuse were verified after restart.
- [x] Fly hosting and the $15 operating budget are approved; the funded service is deployed with one bounded machine and volume.
- [x] Availability and protected operator-attention monitors are configured and Up; a labeled test incident resolved, and the owner confirmed both notification emails.
- [ ] The owner reviews raw findings and the corrected second copy before accepting demonstration content.
- [ ] Confirm the private access-help route before submission.
- [ ] Add the application access code to Devpost's private testing instructions and confirm the final judge arrangement.
- [x] Normal active-host maintenance removed an owned deliberately expired fixture after 67.94 seconds of observation, without affecting another visitor or shared accounting; this did not wait a real 24 hours.
- [ ] Keep funding, capacity, monitor state, and cutoff recovery under operator review through December 15.
- [ ] Verify promotional-credit expiry or maintain the approved paid fallback; no credit validity or platform-enforced $15 cap is assumed.
- [x] Publish the approved branch and open draft PR #1; current runtime CI includes the privacy/Fly configuration corrections and is pinned separately from later documentation edits.
- [ ] Record, review, and approve the public video. Merge and a new release remain separate approvals.
- [ ] The owner confirms personal attestations and explicitly authorizes final entry submission and any other new agreements.

An emergency spending cutoff interrupts live judging. It requires operator intervention to replenish approved funds, revise the approved allowance, or repair abuse. Configured expiry and monitoring do not guarantee future availability; a recording or cached result does not replace an available working service.
