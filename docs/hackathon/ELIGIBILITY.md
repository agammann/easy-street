# Hackathon eligibility and release gates

Checked October 16, 2026 against the [Official Rules](https://nebiusglobalaihackathon.devpost.com/rules) and [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs). The owner subsequently approved the final binding agreement and submission, completed October 16 (Pacific). This checklist records that result and the owner's private confirmations without publishing personal eligibility details.

## Dates and requirements

| Item | Verified requirement | Easy Street evidence or remaining gate |
| --- | --- | --- |
| Submission | August 26, 2026, 9 a.m. Pacific through **October 30, 2026, 10 a.m. PDT** | **Submitted October 16, 2026 (Pacific)** after explicit owner approval of the final binding agreement and submission. Devpost displayed **Project submitted!** and listed the project as submitted to **Nebius x NVIDIA Global AI Hackathon**. |
| Judging | December 1, 9 a.m. through **December 15, 2026, noon PST** | Fly is deployed with approved funding and active monitors; both application-monitor incident/recovery emails were received. Judge instructions were uploaded to the judges-and-organizers-only testing field. Continued operation remains necessary. |
| Track | Best Apps and Agents | Nemotron must perform useful course work through Token Factory. A mocked response or provider selector alone is insufficient. |
| Platform | Nebius runtime use and an NVIDIA open model | The FAQ permits other hosting for the web application. The authenticated catalog, two local live runs, and the funded hosted Nebius sample passed technical checks, including revised prompt v2.1. Raw support gaps and seven corrections are recorded in [content review](CONTENT_REVIEW.md). The owner approved demonstrating the draft with its warnings; teaching-content certification is not claimed. |
| Existing work | Significant updates during the contest window | [CONTEST_CHANGES.md](CONTEST_CHANGES.md) distinguishes the released baseline from adaptation changes. |
| Source | Public open-source repository, setup, necessary assets | MIT [hackathon branch](https://github.com/agammann/easy-street/tree/hackathon/nebius-nemotron-2026) is public with [draft PR #1](https://github.com/agammann/easy-street/pull/1), still unmerged and not a new release. Deployed runtime [0c010c0](https://github.com/agammann/easy-street/commit/0c010c00c160e1cb47c60eea7f758050c23a3831) passed [three-OS CI](https://github.com/agammann/easy-street/actions/runs/38999513875) including Python-only ZIP installation. Separate shutdown [PR #2](https://github.com/agammann/easy-street/pull/2) and cadence correction [PR #3](https://github.com/agammann/easy-street/pull/3) are merged; current operations `main` is `eff7a5351fbaf3be739d112f8cff453c2049c25a`. See [shutdown](AUTO_SHUTDOWN.md). |
| Entry | English description, track, tool feedback, working demo/test build | The [submitted project](https://devpost.com/software/easy-street) contains the saved story, seven technology labels, two images, a thumbnail and working-demo/source/video URLs. Overview, Additional Info and the private testing attachment are saved. The authoritative success banner and hackathon submission listing were observed. |
| Video | Public YouTube demonstration under three minutes | The approved **2:23** [YouTube video](https://youtu.be/32g2rKhPAuE) is verified public, with uploaded English SRT captions marked Done. Anonymous oEmbed returned HTTP 200 and the expected title. YouTube's copyright check reported No issues; this platform check does not replace the license review. |
| Testing | Free judge access until judging ends; private sites supply credentials | Instructions containing only the application access code were uploaded in the judges-and-organizers-only testing field. Access help uses the owner's Devpost profile `agammann`; no personal email or provider/operator key is published. |

The four equally weighted criteria are implementation, design, impact, and idea. Demonstrate a useful workflow, readable evidence review, a specific audience, and substantive Nemotron integration. See the [judging section of the rules](https://nebiusglobalaihackathon.devpost.com/rules).

## Personal confirmations and final agreement

The owner privately confirmed **solo participation, personal eligibility and submission rights**. The two personal-eligibility checkboxes were completed under that confirmation. Personal residence, questionnaire responses and other private details are not reproduced here. These confirmations come from the owner, not an inference from a GitHub profile. After review of the concrete entry and its binding terms, the owner explicitly approved the final agreement and submission. The agreement was accepted and the entry submitted; Devpost's success banner and hackathon submission listing were verified. This does not certify the generated course content or establish future uptime.

## Credits are not guaranteed judging funding

| Offer | Published validity | Operational consequence |
| --- | --- | --- |
| New-account $1 trial | 30 days from signup | A hypothetical October 16 signup expires around November 15, before judging. |
| Builder Program $25 | 90 days from issuance | A hypothetical October 16 issue reaches January 14, 2027; an August 26 issue reaches November 24. Actual account timestamps govern. |
| Hackathon direct $25 code | No exact expiry found in the public offer | Obtain the actual issuance/redemption/expiration terms before counting it. |

Sources: [Token Factory billing](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new), [Builder terms, sections C and H](https://nebius.com/builders-terms-and-conditions), [hackathon resources](https://nebiusglobalaihackathon.devpost.com/resources). Builder credits are restricted to prototyping and experimentation; they are not a production entitlement. Offers can change. No promotional credit is counted as guaranteed judging funding here. Budget conservatively as if credits contribute $0 until verified.

Token Factory billing describes automatic card charging at the configured threshold or for a negative balance at month start. An application allowance does not impose a provider billing cap. The paid fallback is approved only within the existing $3 aggregate inference envelope; any increase or new financial commitment needs further approval. The current [Token Factory legal notice](https://docs.tokenfactory.nebius.com/legal/terms-of-service) points new/non-reserve customers to the [Nebius Services Agreement](https://docs.nebius.com/legal/agreement); do not assume legacy terms apply.

## Release decision

The owner approved Fly hosting and $15 total through December 15 ($8 hosting, $3 aggregate inference including development, $4 contingency). The service is now deployed at **[easy-street-agammann-2026.fly.dev](https://easy-street-agammann-2026.fly.dev)** with runtime source `0c010c0`, on the same 512 MiB machine and 1 GiB volume. Initial zero-budget session-isolation/deletion checks, a funded real sample, restart/source/course persistence, cache reuse, three exports, mobile evidence review, and seven editor saves were exercised on `0e0c17d`. The privacy/configuration replacement passed new CI and local bounded-container acceptance without another provider call. See [verification](VERIFICATION.md) for exact scope and replacement checks.

Three real local/hosted jobs used 20,932 input / 5,801 output tokens, estimated at $0.0115005, with no reservations or uncertain calls. The raw hosted course is `needs_review`; separate inspection found further support gaps. Seven corrections were saved in the second cached copy while leaving the first raw result untouched. All ten edited-copy sections retain review or dependency flags. The owner approved showing this draft with warnings in the video; that approval does not certify the teaching content.

Two approved free Better Stack monitors are Up, checking availability and protected operator attention every three minutes with SSL verification, redirects off, and email-only notifications. A labeled test incident resolved, and the owner confirmed receiving both incident-started and resolved emails through the normal free route. No paid upgrade or external outgoing-email integration was used. The specific monitoring account terms/privacy were approved; other new agreements still need owner authorization. No personal email, judge code, operator token, or provider key belongs in this checklist.

The authorized fixed-app shutdown workflow is active on `main`. Its real cloud rehearsal passed encrypted aggregate-only backup and verification without deleting resources or invoking a model. Actual scheduled runs [39018680800](https://github.com/agammann/easy-street/actions/runs/39018680800) and [39035464465](https://github.com/agammann/easy-street/actions/runs/39035464465) both completed inventory and heartbeat delivery successfully on October 17. Their completion gap was **4 hours, 22 minutes, 56 seconds**, exceeding the heartbeat's unchanged one-hour interval plus 60-minute grace. The owner separately reported an alert timestamped October 16, 23:17 PDT; that receipt does not confirm delivery of the earlier labeled test email. No failure in these two jobs or internal GitHub scheduling cause is established.

[PR #3](https://github.com/agammann/easy-street/pull/3), reviewed at `8296e9e`, passed all three jobs in [CI run 39043362912](https://github.com/agammann/easy-street/actions/runs/39043362912) and merged to `main` at `eff7a5351fbaf3be739d112f8cff453c2049c25a`. It replaces the former hourly minute-37 schedule with minutes **7, 22, 37 and 52**, a nominal 15-minute cadence. **The revised schedule is installed on the default branch; no timed run of it has yet been observed.** The [manual sanity run 39043517427](https://github.com/agammann/easy-street/actions/runs/39043517427) passed real inventory and watchdog delivery on the merged main revision, with future mutations skipped; this does not establish a timed-trigger result. The two-hour missed-check-in threshold and December 9/15, 12:30 p.m. PST date gates remain unchanged; the first normal eligible attempt remains 12:37 p.m. PST. The app was healthy with no added inference at this check. December snapshot disable/cleanup remain future operations; the secondary desktop follow-up is PC-dependent. See [costs and operations](COSTS_AND_OPERATIONS.md) and [automatic shutdown](AUTO_SHUTDOWN.md).

- [x] Both providers pass routine mocked regressions and final runtime CI; see [verification](VERIFICATION.md).
- [x] Three approved real sample jobs record authenticated model, tokens, estimated cost, timing, quotations, and review limitations.
- [x] Revised prompt v2.1 completed a fresh local run; original first-run evidence was preserved.
- [x] Actual hosted desktop/mobile sample/evidence/export and hosted HTTP isolation/deletion checks passed within the recorded scope.
- [x] Hosted source/course/cookie persistence and zero-cost cached reuse were verified after restart.
- [x] Fly hosting and the $15 operating budget are approved; the funded service is deployed with one bounded machine and volume.
- [x] Availability and protected operator-attention monitors are configured and Up; a labeled test incident resolved, and the owner confirmed both notification emails.
- [x] The owner approved the recorded demonstration as a draft with retained warnings; no certified teaching-content acceptance is claimed.
- [x] Access help uses the owner's Devpost profile `agammann`, without publishing a personal email.
- [x] Upload application-code testing instructions in Devpost's judges-and-organizers-only field; provider/operator credentials are excluded.
- [x] Normal active-host maintenance removed an owned deliberately expired fixture after 67.94 seconds of observation, without affecting another visitor or shared accounting; this did not wait a real 24 hours.
- [ ] Keep funding, capacity, monitor state, and cutoff recovery under operator review through December 15.
- [ ] Verify promotional-credit expiry or maintain the approved paid fallback; no credit validity or platform-enforced $15 cap is assumed.
- [x] Publish the approved branch and open draft PR #1; current runtime CI includes the privacy/Fly configuration corrections and is pinned separately from later documentation edits.
- [x] The owner confirmed solo participation, personal eligibility and submission rights privately.
- [x] Record and review the 2:23 video; obtain explicit upload-terms and publication authorization.
- [x] Publish the approved YouTube video, confirm public visibility through anonymous oEmbed, and upload English SRT captions marked Done.
- [x] Save Devpost Overview and Additional Info, including the owner's required private responses.
- [x] Save the public story/details, seven technology labels, two images, thumbnail and demo/source/public-video URLs; retain the private testing attachment.
- [x] Complete the two personal-eligibility checkboxes under the owner's confirmation.
- [x] Obtain action-time owner approval for the final binding Devpost agreement and submission, accept the agreement, submit, and verify **Project submitted!** plus the hackathon submission listing. Completed October 16, 2026 (Pacific).
- [x] Activate the separately approved shutdown workflow on `main` and pass its real non-destructive cloud rehearsal; see [shutdown](AUTO_SHUTDOWN.md) for future execution checks.
- [x] Observe actual successful scheduled inventory/heartbeat runs; record their gap and the missed-check-in limitation separately from application health.
- [x] Merge PR #3's reviewed 15-minute cadence after its three-OS CI passed; installed on `main` at `eff7a5351fbaf3be739d112f8cff453c2049c25a`, with the watchdog threshold and December date gates unchanged.
- [ ] Verify a timed run of the revised cadence; the successful manual sanity run remains separate evidence.

An emergency spending cutoff interrupts live judging. It requires operator intervention to replenish approved funds, revise the approved allowance, or repair abuse. Configured expiry and monitoring do not guarantee future availability; a recording or cached result does not replace an available working service.
