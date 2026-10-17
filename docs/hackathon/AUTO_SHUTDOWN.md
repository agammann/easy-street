# Automatic shutdown after judging

The owner authorized automatic shutdown of the Easy Street Fly deployment after judging. **Status: the primary GitHub Actions workflow is active on `main`, and its real cloud rehearsal passed.** The December snapshot and cleanup stages have not occurred. Two real scheduled runs have now passed; the October 17 missed-check-in investigation and revised cadence are recorded below. The existing application expiry only disables application access; it does not remove Fly resources or stop hosting charges.

The cleanup is restricted to **`easy-street-agammann-2026`**. It must not act on another application, change the inference allowance to create headroom, or call a model. The approved operating envelope remains $15 through December 15, including $3 aggregate inference; scheduling cleanup does not increase it. See [costs and operations](COSTS_AND_OPERATIONS.md).

## Timing and scope

| Stage | Earliest allowed UTC time | Pacific time | Purpose |
| --- | --- | --- | --- |
| Disable new volume snapshots | December 9, 2026, 20:30 UTC | December 9, 12:30 p.m. PST | Allow the configured five-day snapshot retention to elapse before cleanup |
| Remove this deployment | December 15, 2026, 20:30 UTC | December 15, 12:30 p.m. PST | End hosting thirty minutes after the required judging period ends |

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules) currently end judging on December 15 at noon Pacific. Recheck for a changed judging deadline before the destructive stage. The workflow now requests a check every fifteen minutes, at minutes **7, 22, 37 and 52** of each hour. Its first normal eligible runs are therefore December 9 and December 15 at **20:37 UTC / 12:37 p.m. PST**, with later execution possible if GitHub delays a run. The six-day interval provides margin over five-day snapshot retention; it is not proof that snapshots disappeared.

The existing app expiry is `2026-12-16T08:00:00+00:00`, midnight PST at the end of December 15. Resource cleanup is scheduled earlier, after required judging ends. Neither date silently cancels a provider account or revokes its API keys.

## Implemented controls

The [workflow](../../.github/workflows/retire-judging.yml) and [fixed-target controller](../../scripts/fly_shutdown.py) reached the default branch through [PR #2](https://github.com/agammann/easy-street/pull/2), merged at **`089d24c7cff5d0fda89d686361dc7129dc185cf4`**. Workflow **`387359911`** is active. The scheduling-only [PR #3](https://github.com/agammann/easy-street/pull/3) subsequently reached `main` at **`eff7a5351fbaf3be739d112f8cff453c2049c25a`**, changing only the trigger cadence after missed check-ins. Its [CI run 39043362912](https://github.com/agammann/easy-street/actions/runs/39043362912) passed Linux and both Mac runners; the 35 mocked shutdown tests passed locally again. The reviewed change passed all three CI jobs in [run 39001672604](https://github.com/agammann/easy-street/actions/runs/39001672604), including **35 mocked shutdown tests**. This narrow operations merge does not merge the full hackathon application branch.

Actions holds the dedicated application-scoped Fly token under the secret name `EASY_STREET_SHUTDOWN_FLY_TOKEN`; it expires **December 24, 2026, 00:00 UTC**. The independent watchdog URL uses `EASY_STREET_SHUTDOWN_HEARTBEAT`. These are names, not credential values. The cleanup job has read-only repository/Actions permissions. A separate finish job has Actions write permission only to disable this workflow after the controller reports verified retirement. The default-branch schedule runs without the owner's PC.

The controller applies these gates before and during destruction:

1. Check UTC time against the fixed stage deadline and verify the exact application identity. Manual dispatch and retries must preserve these checks.
2. Compare actual Machines and volumes with the approved deployment inventory. Unexpected resources must cause a safe stop and an alert rather than broader deletion.
3. Disable new automatic snapshots at the first stage and inspect retained snapshots at cleanup. Claim zero snapshots only from an empty API inventory or verified disabled/empty evidence recorded before volume deletion. Retained or unverifiable snapshots cause an attention result; the controller can still remove compute, volume and IP resources to stop their charges. That partial result is not proof that snapshot storage disappeared.
4. Preserve the non-content aggregate accounting needed for reconciliation in an encrypted backup. Do not archive visitor originals, course content, tenant databases, session credentials or exports as part of shutdown. A backup failure must block destruction and alert the operator.
5. Remove only the verified Machine, volume and IP allocations, confirming their absence. The free application name is retained. Treat already absent resources as completed steps; a stopped or absent Machine can use the prior verified final accounting artifact for a bounded retry.

The encrypted aggregate record contains non-content usage totals, reservations, uncertainty and provider-health state. It excludes session identifiers and visitor content. The controller reads a consistent SQLite snapshot in memory, validates its narrow schema, and encrypts it with OpenSSL CMS and the owner's [public certificate](../../deploy/shutdown-backup-cert.pem). Only `ledger.cms` and a non-content receipt are uploaded. The private decryption key is not an Actions secret or repository asset. Uncertain charges remain distinguishable from measured spending; no visitor archive is made.

Uploaded artifacts have **30-day retention**. A final backup is required before deletion; the controller downloads the actual artifact, checks its digest, receipt, run identity and certificate, and refuses a rehearsal receipt for destructive cleanup. A previous final artifact may support a partial-cleanup retry for at most **seven days** from its creation. Artifact retention and token expiry do not extend that seven-day acceptance rule. Keep the private decryption key and any accounting needed beyond artifact expiry under the owner's control.

## Real cloud rehearsal

Manual [run 39001965836](https://github.com/agammann/easy-street/actions/runs/39001965836) passed on `main`. It inspected the actual application: **one Machine, one volume, two IP allocations and zero snapshots**. Snapshot changes, inference pause and resource deletion were correctly skipped before their fixed date gates. No provider request or resource mutation was made.

The run uploaded encrypted aggregate artifact **`12089123817`**, SHA-256 **`118631c1afe59921fc414b35c95c81e4078afbcd5a73f3f2ca780a44665fdc13`**, with expiry **November 16, 2026, 04:17 UTC**. The actual artifact was downloaded and verified; a separate local decryption matched the expected aggregate hash. Its accounting remained **two hosted calls, 6,869 input / 2,526 output tokens and $0.0043341 estimated cost**. This rehearsal artifact expires before judging and is deliberately ineligible for deletion; cleanup must create and verify its own fresh final artifact.

## October 17 missed-check-in investigation

The owner reported a **Missed heartbeat** email that started October 16 at **11:17 p.m. PDT**. Better Stack incident **`1033260930`** was verified **Resolved**, with the timeline recording automatic recovery at **October 17, 1:47 a.m. PDT** when check-ins resumed. It was distinct from the earlier labeled failure test. The read-only app check remained healthy, with no operator attention and the same $0.0043341 hosted spending / $2.9884995 remaining estimate; no inference was used to investigate.

The original hourly workflow did run automatically. [Run 39018680800](https://github.com/agammann/easy-street/actions/runs/39018680800) completed inventory and watchdog delivery at **08:47:34 UTC / 1:47:34 a.m. PDT**; [run 39035464465](https://github.com/agammann/easy-street/actions/runs/39035464465) did so at **13:10:30 UTC / 6:10:30 a.m. PDT**. Their **4-hour, 22-minute, 56-second gap** exceeded the two-hour missing-check-in threshold and corresponded to the separately observed **Missed heartbeat** incident **`1033339815`**, listed with a two-hour, 22-minute duration. Neither completed run failed. The API did not expose GitHub's internal reason for missing the intervening expected opportunities. GitHub documents that scheduled events can be delayed or dropped; this is a scheduling-resilience limitation, not evidence of an application outage.

The scheduling-only fix gives four off-peak opportunities per hour. It preserves the **one-hour heartbeat period plus 60-minute grace**, so missing check-ins still alert; no alert was disabled or extended to hide the gap. Date gates, resource identities, backup checks, credentials, permissions and concurrency control are unchanged. The unchanged fixed 12:30 p.m. gates still make 12:37 p.m. the first normal eligible December attempt. GitHub scheduling remains best effort; four opportunities do not guarantee execution. The revised [manual sanity run 39043517427](https://github.com/agammann/easy-street/actions/runs/39043517427) passed on `eff7a5351fbaf3be739d112f8cff453c2049c25a`, including real inventory and watchdog delivery, with all future mutation steps skipped. This is not a timed-trigger acceptance result.

## Monitoring and failure handling

A separate **Better Stack Free heartbeat `510757`** is active with a **one-hour interval and 60-minute grace period**, using owner email only. It watches the primary workflow, separate from the two application monitors. A labeled failure created incident **`1033225577`**, for which the service recorded an email as **Sent**. A recovery POST and the cloud workflow's normal check-in both returned HTTP 200. The incident's **Resolved** state was verified in the service. Owner receipt of this separate heartbeat test email has not been confirmed. The owner's earlier receipt of both application-monitor test emails is separate evidence. No paid monitoring upgrade was configured.

GitHub schedules can be delayed or missed. Failed operations can be retried on the next available scheduled run while their gates and credentials permit; a calendar entry alone is not an on-time shutdown guarantee. The controller reports failure for invalid credentials, changed inventory, an invalid/missing backup, or incomplete cleanup. After verified retirement, the finish job disables the completed schedule, avoiding an indefinitely running expired-token job. If disabling fails, it sends an attention signal to the watchdog.

A secondary Codex desktop follow-up is configured for **Tuesdays at 1:30 p.m. Pacific through December 22**. Its instructions recheck rules, snapshots, cleanup and accounting, then retire this app's two availability/attention monitors and heartbeat, revoke the app-scoped Fly deployment token, and disable the completed workflow after verifying retirement. **This secondary follow-up depends on the owner's PC.** It is not the primary scheduler and does not guarantee cloud-side monitoring retirement. If the PC is off, the owner may receive intentional shutdown/missed-heartbeat alerts and must retire the free monitors and remaining token manually. Dedicated Nebius-key revocation remains separate.

Cleanup failure can leave hosting charges accruing and requires intervention. The emergency inference pause in [costs and operations](COSTS_AND_OPERATIONS.md) prevents new model dispatches but does not solve that hosting-cost exposure. The owner must inspect the failed operation, reconcile any provider uncertainty, and remove only the approved remaining resources. The existing $15 envelope is not a platform-enforced account cap.

## Activation evidence

- [x] Fixed-application workflow and helper reviewed, tested with 35 mocks, and installed on the default branch; workflow active.
- [x] Application-scoped Fly token stored in an Actions secret; recorded expiry December 24, 00:00 UTC.
- [x] Real cloud inventory/rehearsal verified one Machine, one volume, two IPs and zero snapshots without mutation or inference.
- [x] Actual encrypted aggregate-only upload, download verification and separate local decryption passed without retaining visitor data.
- [x] Mock tests cover date gates, partial/stopped-Machine retries, unexpected-resource refusal, failed backups and credential-safe errors.
- [x] Free heartbeat configured; labeled failure recorded email Sent, with HTTP 200 recovery and workflow check-in.
- [x] Verify the heartbeat incident resolved in the service.
- [ ] Confirm owner receipt of this separate heartbeat test email; the earlier application-monitor incident/recovery emails were confirmed.
- [x] Observe real scheduled runs with successful inventory and watchdog delivery: 39018680800 and 39035464465, on the original hourly configuration.
- [ ] Observe a real timed run of the revised fifteen-minute cadence; a manual control check alone does not establish it.
- [x] Fifteen-minute trigger cadence, unchanged two-hour missing-check-in alert, seven-day final-backup retry rule, 30-day artifact retention, expiring credential and PC-dependent secondary follow-up recorded.
- [ ] After December 9: actual snapshot-disable result and subsequent age-out verified.
- [ ] After December 15: final resource absence verified, encrypted accounting retained, and monitoring disposition recorded.

Fly resource cleanup does not revoke the dedicated Nebius key, close the provider account, erase unrelated account usage or prove the final invoice. Review those separately after judging. Do not delete the original development accounting or reset it to make the final totals appear lower.
