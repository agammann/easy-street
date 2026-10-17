# Judging budget and operations

Updated October 16, 2026 (Pacific). The owner approved **Fly hosting and $15 total through December 15**: $8 hosting, $3 aggregate inference including development, and $4 contingency. The approved deployment is running at **https://easy-street-agammann-2026.fly.dev** with private judge authentication and a server-only Nebius key. Provisioning, access-control checks, one restart, a funded hosted sample, cache reuse, and browser editing have been exercised. This records observed operation, not a guarantee of future availability or owner acceptance of generated content.

Three real sample jobs have used **20,932 input and 5,801 output tokens**, estimated at **$0.0115005** in total, within the approved **$1 aggregate acceptance-test ceiling** and $3 inference envelope. The hosted allowance is **$2.9928336**, after subtracting the two development runs from the $3 envelope. Its measured spend is **$0.0043341**, leaving **$2.9884995** with no reserved or uncertain amount. These are application estimates from provider-reported tokens, not verified invoices or actual provider balances. Checked-in templates retain the safe **$0 default**; the deployed allowance is a host-runtime secret override.

Two free Better Stack monitors are active and were observed **Up**. A labeled incident automatically resolved, and the owner confirmed receipt of **both the incident-started and incident-resolved test emails**. The verified team contains only the owner. Normal Free-plan email notifications provide this route; no paid monitoring upgrade or external-email integration was configured. Owner content acceptance, verified promotional-credit expiry, and the manual hosting-bill review/escalation arrangement remain pending. The original $85 proposal was declined; this update makes no new agreement, prepaid purchase, or budget increase. Branch publication and the draft PR are approved and complete; merge, a new release, video publication, and entry submission remain separate approvals.

## Deployed service and budget through December 15

The deployed service uses **one always-running Fly.io shared-CPU Machine, one shared vCPU, 512 MiB RAM, in `iad`, and one encrypted 1 GiB persistent volume**. The inventory has a shared IPv4 address and free IPv6, with no spare Machine, remote builder, dedicated paid IPv4, GPU host, separate database, custom domain, additional worker, or paid support plan. Nebius Token Factory performs inference. The [hackathon FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs) permits hosting the rest of the application elsewhere.

| Configuration | Compute and persistent disk, October 16-December 15 inclusive | Envelope and state |
| --- | --- | --- |
| Deployed Fly `shared-cpu-1x`, 512 MiB, `iad` | ($3.69 + $0.15) x 61/30, approximately **$7.81** | **$15 approved**: $8 hosting, $3 aggregate inference, $4 contingency |
| Fly `shared-cpu-1x`, 1 GiB, `iad` | ($6.70 + $0.15) x 61/30, approximately **$13.93** | **$20 unapproved alternative**; no upgrade performed |
| Render Starter `0.5c-512mb`, one 1 GB disk | ($7 + $0.25) x 61/30, approximately **$14.74** | **$20 unapproved alternative**; no Render service deployed |
| Original Render `1c-2g`, one 1 GB disk | ($25 + $0.25) x 61/30, approximately **$51.34** | Historical **$85 proposal declined** |

Official prices checked October 16: [Fly Machine, volume, network, snapshot, and IP prices](https://docs.fly.io/about/pricing), [Render pricing](https://render.com/pricing), and [Render compute-plan IDs](https://render.com/docs/compute-plans). The 30-day conversion is a planning approximation. Actual charges depend on service time, region, account usage, taxes, and metered extras; later provisioning reduces the whole-period estimate. Hosting charges accrue even when the inference allowance is zero. Contingency is not permission to add services, upgrade, or exceed the approved total.

Fly's shared IPv4/IPv6 and first ten single-host certificates currently have no separate charge. North American public egress is $0.02/GB; an assumed 10 GB adds $0.20, not a free allowance. Snapshot storage is $0.08/GB-month with the first 10 GB currently included each month. The configured one-volume, five-day rotation should fit that inclusion in isolation, but other account usage and actual retained bytes still govern billing. Volume storage remains billable while stopped or unattached, and stopped Machine root filesystems can incur storage charges. Do not leave obsolete resources behind.

Fly's [billing documentation](https://docs.fly.io/about/billing) describes ordinary metered card billing and an alternative prepaid purchase with a **$25 minimum**. The approved envelope uses metered billing; no prepaid purchase was made. A new $25 purchase would exceed the approved $15 and require revised approval. Provider invoices remain unverified; private account and payment details are excluded from this public record.

Fly's [cost-management documentation](https://docs.fly.io/about/cost-management) states that native billing alerts are unavailable and free allowances do not cap charges. **No automatic $15 Fly account spending cap or hosting-cost alert is configured.** The application ledger controls inference, not compute, disk, egress, or unrelated account activity. A named owner route and manual review cadence for the current-month bill and resource inventory remain to be recorded. Better Stack application alerts do not fill that financial-control gap.

One Machine and volume provide no built-in replication. A failure or deployment can interrupt access; see [Fly availability](https://docs.fly.io/apps/app-availability). The intended working period runs through December 15, with application expiry at the end of that day. Monitoring and configuration do not guarantee availability throughout the period. If 512 MiB proves insufficient, obtain approval for a different plan before upgrading.

The separate local constrained profile passed under **512 MiB RAM and 0.5 CPU**, including PDF/DOCX/TXT samples, a three-module offline course and 100 isolated visitor applications. Whole-test peak was **100.262 MiB**, memory after 100 visitors was **93.078 MiB**, with no OOM event or kill. These fixture measurements are not a production memory ceiling. Actual Fly acceptance adds the host-specific evidence below.

## Inference estimate and measured use

The verified model is **`nvidia/nemotron-3-super-120b-a12b`**, through `https://api.tokenfactory.nebius.com/v1/`. The implementation's October 16 [Token Factory catalog/pricing](https://tokenfactory.nebius.com/) snapshot is **$0.30/million input and $0.90/million output tokens**, with no cached-token discount assumed. Application-cache reuse makes no inference request. Recheck rates and model availability before future paid work.

```text
estimated_usd = input_tokens x 0.30 / 1,000,000
              + output_tokens x 0.90 / 1,000,000
```

| Real sample | Input tokens | Output tokens | Estimate from reported use | Measured job time |
| --- | ---: | ---: | ---: | ---: |
| First local acceptance | 5,984 | 1,397 | $0.0030525 | 8.62 seconds |
| Local prompt-v2.1 follow-up | 8,079 | 1,878 | $0.0041139 | 10.50 seconds |
| **Development subtotal** | **14,063** | **3,275** | **$0.0071664** | Two jobs |
| Funded Fly sample: generation and support review | 6,869 | 2,526 | $0.0043341 | 15.8418 seconds |
| **Combined development and hosted use** | **20,932** | **5,801** | **$0.0115005** | Three jobs |

The hosted sample completed **two provider calls** and ten sections, including three quiz questions. Its 31 attached quotations resolve exactly to the original licensed chapter. The course is **needs review**, with a visible missing-evidence flag on its uncited introduction. Further inspection found unsupported assurance wording and citation/precision gaps elsewhere. Exact quotations and a successful provider response do not establish complete factual support.

An equivalent second hosted course reused the cache with **zero additional provider calls and no shared-ledger change**. Seven text-only corrections were then saved to that cached copy through the real browser editors, taking its version from 5 to 12 without inference. The original first course and exports remained unchanged. The edited copy retains manual-edit and dependency review flags; **owner content acceptance remains pending**. This is evidence of the editing/review workflow, not a fresh support-review result or owner sign-off.

The first two runs used the original persistent development-test ledger. The hosted service has its own persistent operator ledger; the combined figures above reconcile both locations against the aggregate approval. The active hosted limit is **$2.9928336**, spend **$0.0043341**, and remaining allowance **$2.9884995**. Further development charges must reduce the remaining approved hosted capacity; do not treat the two ledgers as separate grants or reset either to create headroom. Do not presume the entire $1 acceptance ceiling was spent.

For planning only, a small uncached course using 20,000 input and 12,000 output tokens across generation and review would cost **$0.0168**; 150 such courses would cost $2.52. This is a hypothetical workload, not a measured average or guarantee. Larger selections, more modules and regeneration consume more tokens. Conservative reservations govern admission and can exceed typical measured use.

Provider invoices and account usage are the financial authority. Malformed responses can be billable; lost usage or timeouts can leave an uncertain charge. Preserve uncertainty reservations and never automatically repeat a request to make a test pass. Both adapters disable SDK retries. The [live acceptance harness](../../scripts/live_nebius_check.py) uses an exclusive safety lock and durable accounting outside the repository; failures retain the lock for deliberate review. An old PID or elapsed time does not prove a request was unbilled.

## Credit validity and paid fallback

**Count promotional credit as $0 guaranteed** until private account records establish amount, issuance, expiry, permitted use, and availability for this model. No account-verified expiration timestamp is configured. Public offer terms alone do not establish funding through December 15.

| Offer | Published validity | Limit of the current evidence |
| --- | --- | --- |
| New-account $1 trial | 30 days from signup | An October signup would expire before judging ends; verify the actual expiration privately |
| Builder Program $25 | 90 days from issuance | No account-verified expiry timestamp is configured; do not infer issuance/expiry from a generic offer |
| Direct hackathon $25 offer | Public offer does not establish an exact expiry | Obtain its actual account/offer terms; do not borrow the Builder validity rule |

Sources: [Token Factory billing](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new), [Builder terms](https://nebius.com/builders-terms-and-conditions), and [hackathon resources](https://nebiusglobalaihackathon.devpost.com/resources). Builder terms restrict credits to qualifying prototyping/experimentation and allow changes or suspension. An observed grant is not a blanket production entitlement.

The paid fallback stays within the approved **$3 aggregate inference envelope**. After all measured development and hosted use, **$2.9884995** remains by application estimates, subject to invoice reconciliation and any further approved charges. No new agreement, payment method or top-up is accepted by this document. Nebius describes automatic charging at a billing threshold or a negative balance at month start; an app allowance does not cap unrelated account activity. An optional `NEBIUS_CREDIT_EXPIRES_AT` must contain an account-verified timestamp. Until that is known and configured, the monitor cannot provide a meaningful credit-expiry warning.

## Runtime configuration and deployed evidence

Configuration sources are the [Dockerfile](../../deploy/Dockerfile), [Fly template](../../deploy/fly.toml), [Render alternative](../../deploy/render.yaml), [Compose rehearsal](../../deploy/compose.judging.yaml), and [secret-free environment template](../../deploy/.env.judging.example). The reusable templates keep allowance zero. The active deployment overrides that setting in Fly's runtime secret environment; the provider key, judge-password hash and read-only operator token also remain runtime secrets.

| Control | Deployed or configured value |
| --- | --- |
| Origin | `https://easy-street-agammann-2026.fly.dev`, exact HTTPS origin |
| Shared inference | Limit $2.9928336; measured remaining $2.9884995 at this checkpoint |
| Session allowance | $0.50; operator assistance must keep legitimate judging possible |
| Concurrency | At most 2 provider calls; one Uvicorn worker and one instance |
| Visitor capacity | At most 100 temporary sessions |
| Upload/source | 5 MiB; one readable chapter, at most 100,000 characters/1,000 passages; bounded PDF expansion/work |
| Course | At most 3 modules, 3 assignments and 3 quizzes |
| Application retention | 24 hours configured; actual scheduled cleanup passed with an isolated expired-session fixture; active work can delay removal |
| Volume snapshots | Daily snapshots configured with five-day retention |
| Application expiry | `2026-12-16T08:00:00+00:00`, midnight PST at the end of December 15, after judging ends at noon |

The **initial funded-host acceptance** used source **`0e0c17d0915e815754f547fbb7ecc388bdaa6c11`**, with green [CI run 38997180882](https://github.com/agammann/easy-street/actions/runs/38997180882). Its historical local Docker image ID is **`sha256:c5766ffd14db8851a766bed0e72aca273ec6f01a0cdadc560cb780217ae50997`**; its registry manifest is **`sha256:2ab6741c4d0c9e6ec406ff8d3eb4573f921353d69f6936ac945407910cdaf25b`**. These identify different image objects and must not be interchanged. The two funded hosted calls above remain evidence from this initial deployment.

The **current confirmed deployment** uses source **`0c010c00c160e1cb47c60eea7f758050c23a3831`** on the same Machine and volume, with **1/1 Fly health checks passing**. Its local/registry OCI index is **`sha256:7242015d8cdd49d910f64b6c1c16dc5b458594072bffab0c2330411cdb4f0592`**; Fly reports the deployed platform manifest **`sha256:9b432a9effddd554fbac7f105eb15f470a9611da5e47ad0c0f824fc4d48552fc`**. The index and platform manifest identify different objects. All three jobs in [CI run 38999513875](https://github.com/agammann/easy-street/actions/runs/38999513875) passed: Linux had 279 backend tests pass, each macOS job had 278 pass and one skip, and all jobs passed the 49 frontend tests, production build, packaging and installation checks. The 117-file source ZIP has SHA-256 **`30d1acc83249add63385511874fd4af6912aa30a61a85e6c71feb474e502604f`**. The replacement also passed local acceptance under 512 MiB RAM and 0.5 CPU without inference.

This replacement clarifies active 24-hour workspace retention versus retained backups, links the retention details, and describes deletion of active files without implying that all backup copies disappear. The final deployed-server audit passed **31/31 checks**; original source/course hashes and the two-call ledger remained unchanged, with no reserved or uncertain amount. Browser checks verified the revised retention copy, persisted version-12 ten-section course, and a 390-pixel layout without horizontal overflow. These replacement checks made **zero additional provider calls**. Provider/accounting code, the measured cost, allowance and remaining budget are unchanged; CI, deployment identity, browser checks and funded inference remain separate evidence.

The actual mounted directory was verified owner/group **10001:10001**, mode **0700**, and writable by the nonroot application. One real host restart preserved the authenticated cookie, source, and complete course. Initial zero-allowance host checks verified two independent sessions, CSRF/Origin controls, upload isolation, a pre-dispatch spending rejection, offline ten-section generation, three exports, and deletion of only the test workspaces. The subsequent funded sample and cache check above established actual remote inference. Export checks found no sensitive credential fields or known credential values; no credential values are published here.

A separate owned cleanup fixture was marked expired after its source and lack of jobs/provider calls were verified. Its source then returned 401, and the normal minute-scale maintenance removed both the session record and tenant directory. No forced cleanup, deletion endpoint or system-clock change was used, and other visitor data and the operator ledger remained unchanged. This verifies the deployed scheduled cleanup with a test expiry; it does not claim that a full 24-hour retention period elapsed.

The Fly volume bootstrap was completed under the approved deployment: a temporary same-group sleeping process allowed initialization of the dedicated mount, then the normal nonroot app replaced it. The change was limited to that mount, nonrecursively, and the inventory was checked for one Machine and volume. For a future fresh disk, verify the exact mount and that it is empty before initializing ownership; do not apply that procedure blindly to an existing data volume. A release command cannot initialize a volume it does not mount. See [Fly configuration](https://docs.fly.io/reference/configuration), [administrative console](https://docs.fly.io/flyctl/cmd/fly_ssh_console), and [process groups](https://docs.fly.io/launch/processes).

For future approved updates, build locally and use `fly deploy --config deploy/fly.toml --ha=false --local-only` with the correct private app configuration. Verify actual resources afterward: the TOML is not a Machine-count ceiling. Do not horizontally scale the SQLite-backed workspace or its in-process concurrency gate. Do not add a remote builder or paid resource without approval.

Application deletion removes active workspace data once work stops; an existing host snapshot can retain it for the configured five days. Snapshot restoration can roll back accounting. Reconcile later provider charges and uncertain reservations before reopening inference after a restore. A successful restart is not a tested snapshot restore or a guarantee of immediate backup erasure.

Local BYO installations remain separate. [scripts/configure_nebius.py](../../scripts/configure_nebius.py) saves a masked key to ignored local configuration without making an API call. [scripts/configure_judging.py](../../scripts/configure_judging.py) creates a judge hash/operator token with allowance zero and refuses to overwrite its private output. Never copy development environment files into the image or expose keys, judge credentials or operator tokens through Git, build arguments, URLs, logs, screenshots or exports. Judges receive only the application access code through private instructions.

## Health, alerts and actual monitoring

The account is on **Better Stack Free**. Two active monitors were observed **Up**, using HTTPS **GET**, three-minute checks, TLS verification on, redirects off, and account email notifications only. No paid plan, SMS, calls, push service or public status page was enabled.

| Monitor | Check | Authentication and result |
| --- | --- | --- |
| `5085474` | `/health/ready` returns 2xx | No credential; observed Up |
| `5085477` | `/api/operator/status` contains `"needs_attention":false` | Private read-only Bearer header; observed Up |

The read-only operator token is held only in private monitor configuration. Better Stack does not receive the Nebius key or judge access code. Never place monitor credentials in a URL, plaintext command argument, public guide, screenshot or response dump. References: [free tier](https://betterstack.com/pricing), [check frequency](https://betterstack.com/docs/uptime/check-frequency/), [keyword/custom-header API](https://betterstack.com/docs/uptime/api/create-a-new-monitor/), and [request authentication](https://betterstack.com/docs/uptime/request-parameters-headers-and-http-authentication/).

- `/health/live` reports process liveness and never calls a model.
- `/health/ready` reports infrastructure readiness. It can remain HTTP 200 while `generation_available` is false; HTTP status alone does not detect exhausted funds.
- `/api/operator/status` reports allowance/uncertainty, observed provider-stage failure, deployment expiry, verified credit expiry within seven days, missing configuration and cleanup failures. Provider health reflects actual adapter outcomes, not synthetic inference or factual correctness. It does not read the provider credit balance or Fly bill.

The low-allowance threshold is the final **20% of the enabled hosted limit**, approximately **$0.5986** at the current $2.9928336 limit, with a $0.10 minimum. The operator keyword check observes that attention flag without generating a course. Credit-expiry checks become useful only after an actual expiry timestamp is verified and configured. Application monitoring is not provider-balance or hosting-cost monitoring.

A labeled test produced incident **`1033213383`**, which changed from Down to automatically resolved. The owner explicitly confirmed receipt of **both the new-incident and incident-resolved emails**. The account's team was verified to contain one member, the owner, and both three-minute monitors remain Up. This verifies the normal free email delivery/recovery route with a labeled test; it does not continuously test a model or establish the provider's actual credit balance.

Attempting to add an outgoing integration for an external email address displayed an upgrade requirement while the account remained Free. **No paid upgrade or external-email integration was configured or needed for the verified route.** The account's normal free email notifications reached the owner. The approved scope remains free monitoring and labeled test alerts. Other agreements or paid services require separate approval.

| Operational evidence | Current state |
| --- | --- |
| Availability and authenticated attention checks | Two configured monitors, observed Up; three-minute interval |
| Labeled outage/recovery incident | Test incident automatically resolved |
| Outage email | Owner confirmed receipt of the incident-started test email |
| Recovery email | Owner confirmed receipt of the incident-resolved test email |
| Alert recipient | Verified one-member team, owner only; no personal address published |
| External-email integration | Upgrade-gated; not configured; no upgrade purchased |
| Operator response/escalation route | Owner arrangement still to be recorded |
| Fly bill review | Manual review cadence/response route pending; no native alert or hard $15 cap |
| Provider credit expiry | Official offer terms documented; account-specific expiry unverified |

For a manual diagnostic, securely supply the operator token in the process environment and run:

```sh
python scripts/demo_healthcheck.py --url https://easy-street-agammann-2026.fly.dev --operator --expect-generation
```

The diagnostic prints booleans, never credentials or raw responses. Exit 0 means its selected checks passed, 1 means attention, and 2 means invalid local configuration. It makes GET requests only and does not invoke a model, retry, notify or install monitoring. Routine mocked tests and a one-time diagnostic are distinct from the configured monitors and delivery evidence above.

## Emergency cutoff and recovery

The persistent server allowance counts measured spend plus reservations and blocks new paid work at its limit. Templates start at zero; the deployed allowance is now funded only within the approved inference envelope. Cancellation may not stop an in-flight charge. An ambiguous call remains reserved rather than being silently replayed. Provider-account controls and usage reconciliation remain necessary.

| Existing safeguard | Cost-control behavior |
| --- | --- |
| Persistent allowance checks | Reserve conservative estimated costs and check the shared allowance before each provider call; deletion of a visitor workspace does not erase shared accounting |
| Bounded work | Hosted chapter/module limits, 8,000 generation and 3,500 verification output tokens per call, and at most two concurrent provider calls constrain each request |
| Duplicate and cache handling | Reuse matching request IDs and saved results within the visitor workspace instead of repeating inference |
| Retry and uncertainty handling | No automatic SDK retries; unresolved billing outcomes retain reservations for review |
| Low-allowance warning and emergency pause | The authenticated attention check feeds the tested email route; the pause below blocks new dispatches without resetting the ledger or stopping hosting charges |

**Reaching the cutoff interrupts live judging and requires operator intervention.** Record the owner's response route in private testing instructions before offering final judge access. On an alert, inspect the protected ledger and provider dashboard, retain uncertain reservations, stop abusive access if present, and obtain approval for additional funds. Adjust allowance only within the approved total. Verify a fresh judge workflow and the monitor's recovery afterward. Never reset accounting or replace a working service with a recording to hide an interruption.

For an emergency pause on the existing deployment, the authenticated operator can run:

```sh
fly secrets set EASY_STREET_DEMO_BUDGET_USD=0 --app easy-street-agammann-2026
```

This changes a non-credential allowance setting and restarts the existing service. It preserves the persistent ledger and prevents new paid dispatches; an already dispatched request can still be billed. The protected attention monitor will alert. It does not stop Fly hosting charges. Before reopening, reconcile both development and hosted charges, choose a limit within the remaining approved total, and confirm the health check and email recovery.

Keep enough headroom before December 1. Judges must not need a personal provider account, key, payment or ordinary quota renewal. If a session allowance or capacity cap obstructs legitimate testing, the operator must provide a fresh testing session or an approved adjustment promptly. Monitoring, receipts and an operator response must stay operational; the current setup alone cannot guarantee service through December 15.

The owner authorized automatic Fly cleanup after judging. The [shutdown procedure](AUTO_SHUTDOWN.md) is now active on `main` at **`089d24c7cff5d0fda89d686361dc7129dc185cf4`**, after [PR #2](https://github.com/agammann/easy-street/pull/2). Its date gates allow snapshot disable from **December 9 at 20:30 UTC** and retirement from **December 15 at 20:30 UTC / 12:30 p.m. PST**, thirty minutes after judging ends. Hourly checks occur at minute 37, so the first normal eligible runs are **12:37 p.m. PST** on those dates; GitHub delays remain possible. The workflow runs independently of the owner's PC and disables its completed schedule only after verified retirement.

The exact-app controller passed 35 mocked tests and all three [CI jobs](https://github.com/agammann/easy-street/actions/runs/39001672604). Real cloud [rehearsal 39001965836](https://github.com/agammann/easy-street/actions/runs/39001965836) passed inventory of one Machine, one volume, two IPs and zero snapshots, encrypted aggregate-only upload/download verification, and a separate successful local decryption. All date-gated mutations were skipped; its rehearsal receipt cannot authorize deletion. It made no provider calls: hosted accounting remains two calls and **$0.0043341**, combined use **$0.0115005**, with the same allowance and remaining budget. The rehearsal artifact has 30-day retention and expires before judging; the actual cleanup requires a fresh verified final artifact. No visitor documents or courses are archived.

The app-scoped Actions token expires **December 24, 00:00 UTC**. Free Better Stack heartbeat **`510757`** watches the hourly controller with a one-hour interval, 60-minute grace and owner email. Labeled failure incident **`1033225577`** recorded email Sent; its recovery POST and the workflow check-in returned HTTP 200. The incident was verified **Resolved**; owner receipt of this new heartbeat email remains unconfirmed; the earlier application-monitor email confirmations are separate. A scheduled-trigger run and the future December actions have not yet been observed.

A secondary desktop follow-up is active on Tuesdays at **1:30 p.m. Pacific through December 22** to verify cleanup, retire the free monitors/heartbeat and remaining app-scoped token, and check workflow retirement. That follow-up depends on the owner's PC. Primary cleanup does not automatically pause Better Stack in the cloud; if the secondary cannot run, intentional shutdown alerts can continue until the owner retires those monitors. This configuration adds no paid service or budget increase.

**Application expiry does not stop Fly billing.** A failed cleanup can leave charges accruing and requires intervention; the procedure is not a platform-enforced account cap or an on-time execution guarantee. It archives no visitor documents or courses. Revoke the dedicated Nebius key and reconcile final provider charges separately after judging; Fly resource cleanup alone does neither. Do not leave the Machine or volume running on the assumption that the application's end date cancels them.
