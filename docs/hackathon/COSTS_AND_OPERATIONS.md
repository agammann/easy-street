# Judging budget and operations

Prepared October 16, 2026. The owner approved **Fly hosting and $15 total through December 15**: $8 hosting, $3 aggregate inference including actual development charges, and $4 contingency. Deployment is approved **conditional on final checks and a passing live Nebius test**. Two real Nebius runs remain within the original **$1 aggregate development-test cap**: the first completed ten sections in **8.62 seconds** for **$0.0030525**, and the v2.1-prompt follow-up took **10.5 seconds** for **$0.0041139**, all application estimates from reported tokens. Aggregate estimated cost is **$0.0071664**. The development key stays private; the provider invoice is unverified, and **owner content acceptance remains pending** despite zero automatic flags. The original $85 proposal was declined. Fly CLI authentication and strict configuration validation passed; no paid hosting resources are provisioned. The owner approved the specific Better Stack free-account Terms/Privacy and sign-in email; signup was confirmed and a magic link sent for owner sign-in. Monitors remain **not configured or delivery-tested**. Other account agreements/payment steps stay under the owner's private control. Branch publication and draft PR creation are approved and complete. Merge, a new release, video publication, other new agreement acceptance, and entry submission remain unapproved. The judging runtime generation allowance stays $0 until the deployment conditions pass.

## Proposed service and budget through December 15

The approved host is **one always-running Fly.io shared CPU Machine in `iad`, 512 MiB RAM, and one 1 GB volume**, subject to final acceptance and the passing live Nebius test. The application calls Nebius Token Factory for inference. No GPU host, separate database, custom domain, paid dedicated IPv4 address, additional worker, or paid support plan is included. The [hackathon FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs) permits hosting the remainder of the application elsewhere.

| Candidate | Compute and persistent disk, October 16–December 15 inclusive | Total envelope and approval state |
| --- | --- | --- |
| Fly `shared-cpu-1x`, 512 MiB, `iad` | ($3.69 + $0.15) × 61/30 ≈ **$7.81** | **$15 approved**: $8 hosting, $3 aggregate inference, $4 contingency; deployment conditional on final checks/live test |
| Fly `shared-cpu-1x`, 1 GiB, `iad` | ($6.70 + $0.15) × 61/30 ≈ **$13.93** | **$20 unapproved alternative**: $14 hosting, $3 aggregate inference, $3 contingency |
| Render paid Starter `0.5c-512mb`, one 1 GB disk | ($7 + $0.25) × 61/30 ≈ **$14.74** | **$20 unapproved alternative**: $15 hosting, $3 aggregate inference, $2 contingency |
| Original Render `1c-2g`, one 1 GB disk (historical proposal) | ($25 + $0.25) × 61/30 ≈ **$51.34** | **$85 declined**; no longer the checked-in Render plan |

The approved $3 inference envelope includes development usage. Subtracting both runs' aggregate **$0.0071664 application estimate** leaves at most **$2.9928336** for hosted inference **before further approved deployment-acceptance or development calls**. The invoice remains the authority; reduce that allowance for any additional charges before enabling the deployment, after its acceptance conditions pass. Do not presume the full $1 test ceiling has been spent. No promotional credit is deducted; verified expiry remains a prerequisite for counting it. The 30-day conversion is a planning approximation; actual bills use provider rates, service time, region, account usage, taxes, and metered extras. A later launch reduces expected cost. Contingency is not permission to add services, upgrade, or exceed the approved $15 total.

Official prices checked October 16: [Fly Machine, volume, network, snapshot, and IP prices](https://docs.fly.io/about/pricing), [Render pricing](https://render.com/pricing), and [Render compute-plan IDs](https://render.com/docs/compute-plans). Fly prices vary by region; `iad` is used for this quote. Its shared IPv4/IPv6 and first ten single-host certificates currently have no separate charge. North American public egress is $0.02/GB, so an assumed 10 GB would add $0.20; this is a workload estimate, not a free allowance. Snapshot storage is $0.08/GB-month with the first 10 GB currently included each month. A one-volume five-day snapshot rotation should fit that inclusion in isolation, but other account usage and actual retained bytes must be checked. Volume storage is charged even while stopped/unattached; stopped Machine root filesystems can also incur storage charges. Do not leave obsolete Machines, volumes, or builders behind.

The Fly proposal disables idle stopping and uses one Machine with one persistent volume. Approved deployments must build with local Docker and `--local-only`, use `--ha=false`, and independently verify that no spare Machine or remote builder was created. [Fly's CLI reference](https://docs.fly.io/flyctl/cmd/fly_deploy) documents those options. The [availability documentation](https://docs.fly.io/apps/app-availability) explains the single-volume setup and lack of built-in replication. One Machine can fail or briefly go offline during deployment; monitoring and an operator response are needed. This is a small judging service, not an availability guarantee.

The latest local container acceptance passed with **512 MiB RAM and 0.5 CPU**, covering login, TXT upload, isolation, zero-budget cutoff, explicit offline exports, restart, and deletion. A separate profile passed PDF/DOCX/TXT sample uploads, a three-module offline course, and 100 isolated visitor applications. Whole-test peak was **100.262 MiB**, memory after 100 visitor applications was **93.078 MiB**, and no OOM event or kill occurred. These fixtures do not prove worst-case uploads, actual host behavior, or a real provider response. Actual host capacity, disk permissions, and the full real generation workflow remain deployment acceptance gates. If 512 MiB fails those checks, seek approval for the 1 GiB option rather than silently upgrading. The [Render alternative](../../deploy/render.yaml) now uses the tested smaller shape, `0.5c-512mb`; the original 2 GB proposal above is retained only as history.

Fly's [billing documentation](https://docs.fly.io/about/billing) says most accounts need an active valid credit card; an alternative prepaid-credit purchase has a **$25 minimum**. The approved $15 envelope assumes ordinary metered card billing, **not** a $25 credit purchase. A new $25 upfront purchase would exceed it and requires revised approval. A card verification hold can also appear temporarily. The owner handles payment/account steps privately; no agreement or credit purchase is accepted by this preparation. Do not count a trial or a free day toward judging availability.

Fly is pay-as-you-go with **no separate platform subscription fee** for this proposed configuration. Its [cost-management documentation](https://docs.fly.io/about/cost-management) says it currently provides **no native billing alerts** and that free allowances do not cap charges. There is **no automatic $15 account spending cutoff configured or established here**. The application ledger constrains inference, not Fly compute/storage/egress or other account activity. A recorded owner route and manual review of the dashboard's current-month bill and resource inventory are still pending. Confirm that review arrangement before provisioning; do not describe the $15 approval as a provider-enforced billing cap or promise automatic hosting-cost alerts.

Render's [free service](https://render.com/docs/free) sleeps after 15 idle minutes and loses local SQLite/uploads on restarts or spin-down because free services cannot attach persistent disks. Losing the shared accounting ledger would undermine the cutoff, so it is not a drop-in judging host. [Railway Hobby](https://docs.railway.com/pricing/plans) has a $5 monthly minimum including $5 usage, but metered RAM/CPU can exceed it; it is not a fixed $5 cap. A free [Cloudflare Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) would depend on the owner's PC staying awake, powered, connected, and running, with a temporary URL and no uptime SLA. These alternatives do not currently offer a better verified judging arrangement. Fly's limited new-account trial is not a free plan through December 15.

Persistent storage is mandatory for accounting and temporary workspaces across restarts. Keep one Uvicorn worker and one service instance; do not horizontally scale SQLite-backed workspaces or the in-process concurrency gate. Render's [disk limitations](https://render.com/docs/disks) also restrict its service to one instance and cause brief deployment downtime.

## Inference estimate and measurement

Verified live model: **`nvidia/nemotron-3-super-120b-a12b`**, through `https://api.tokenfactory.nebius.com/v1/`. The implementation's October 16 catalog pricing is **$0.30/million input tokens and $0.90/million output tokens**, with no assumed cached-token discount. Application cache reuse makes no inference request. Recheck the official [Token Factory catalog/pricing](https://tokenfactory.nebius.com/) and authenticated availability before future runs.

Cost calculation:

```text
estimated_usd = input_tokens × 0.30 / 1,000,000
              + output_tokens × 0.90 / 1,000,000
```

For planning only, an uncached small course using 20,000 input and 12,000 output tokens across generation and review would cost about **$0.0168**. At that assumed average, 150 courses would be $2.52. This is a hypothetical workload, not a measurement or service guarantee. Larger source selections, multiple modules, and section regeneration consume more tokens. The application's conservative preflight reservation may be much higher than typical actual usage and governs admission.

| Approved live-test field | Recorded result |
| --- | --- |
| Approval and maximum | Up to **$1 total approved October 16, 2026**, within the approved $3 aggregate inference/$15 Fly envelope; development key saved privately. Final content/deployment acceptance remains open. |
| Exact model and runtime endpoint | Authenticated catalog and real call verified `nvidia/nemotron-3-super-120b-a12b` at `https://api.tokenfactory.nebius.com/v1/` |
| First run: source and result | Original garden sample; **ten sections completed** |
| First run: generation usage and application estimate | **2,189 input + 1,010 output tokens; $0.0015657** |
| First run: support-review usage and application estimate | **3,795 input + 387 output tokens; $0.0014868** |
| First run: total and duration | **5,984 input + 1,397 output tokens; $0.0030525; 8.62 seconds**; original evidence retained unchanged |
| Follow-up: v2.1 prompt | **8,079 input + 1,878 output tokens; $0.0041139; 10.5 seconds** |
| Aggregate reported usage and application estimate | **14,063 input + 3,275 output tokens; $0.0071664**, within the original $1 test cap; provider invoice not verified |
| Aggregate accounting | No outstanding reserved/uncertain amount recorded |
| Human content review | **Owner acceptance pending, not fully passed.** Both runs had zero automatic flags; this did not establish complete support/coverage. |
| Cached repeat | Consult the live acceptance record before claiming no extra request/charge; not separately established by this table |

Manual review of the first run found that an introduction cited only a title and that the wording “ensure proper absorption” overstated the source. The original evidence is retained unchanged. The v2.1-prompt follow-up removed that assurance and added substantive citations, but inspection still found partial source coverage and approximate-precision issues despite zero automatic flags. These findings remain distinct from successful API execution and schema validation. Owner review remains pending; neither run establishes complete educational-content acceptance or completion of the deployment's live-test condition.

Provider-reported tokens produce the application estimate; the provider's invoice and account usage are the financial authority. A received malformed response can still cost money. Timeouts or lost usage can have uncertain billing outcomes. Do not clear their reservations or automatically repeat them merely to make a test pass.

The prepared [live acceptance harness](../../scripts/live_nebius_check.py) writes private durable accounting outside the repository and creates an exclusive `active.lock` before checking the model/running generation. Successful completion releases its own matching lock. Failure or interruption retains it: stop any active process, review the ledger, provider usage, and outcome, and only then decide whether manual removal is safe. An old PID or elapsed time does not prove an unbilled request. Do not delete the lock, create a new evidence directory, reset the ledger, or rerun automatically to bypass this safeguard. The script's human content-review field remains pending until a person inspects the generated claims against the chapter.

## Credit validity and paid fallback

Count promotional credit as **$0 guaranteed** in the approval proposal until the actual account records show amount, issuance, expiry, permitted use, and availability for this model. Published offers are not proof of a grant.

- Signup trial: $1 valid for 30 days; October 16 signup would expire around November 15, before judging. [Official billing documentation](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new).
- Builder Program: $25, 90 days from issuance. October 16 issuance would reach January 14, 2027; August 26 issuance would expire November 24. Its [terms](https://nebius.com/builders-terms-and-conditions) restrict usage to qualifying prototyping/experimentation and permit changes or suspension.
- Direct hackathon $25 offer: public [resources](https://nebiusglobalaihackathon.devpost.com/resources) do not establish a precise expiry. Obtain actual account/offer terms; do not borrow the Builder offer's 90-day rule.

The approved paid fallback is the remaining portion of the aggregate $3 inference envelope: at most **$2.9928336** after the two test estimates, reduced by further approved charges and subject to final content/deployment acceptance and owner-controlled private setup. No card is added or topped up here. Nebius describes automatic card charging at a billing threshold or negative balance at month start; an app allowance cannot cap other account activity. Use a dedicated demo project/key and reconcile its dashboard with the ledger. An optional `NEBIUS_CREDIT_EXPIRES_AT` records a verified timestamp only; it does not create or extend credit.

## Prepared configuration

Files: [Dockerfile](../../deploy/Dockerfile), [Compose rehearsal](../../deploy/compose.judging.yaml), [Fly proposal](../../deploy/fly.toml), [Render alternative](../../deploy/render.yaml), and [secret-free environment template](../../deploy/.env.judging.example). The templates specify these defaults:

| Control | Prepared value |
| --- | --- |
| Shared inference allowance | **$0** until final content/deployment checks pass; at most $2.9928336 remains from the approved $3 after both test estimates, before further approved acceptance/development calls |
| Session allowance | $0.50; operator assistance must keep legitimate judging possible |
| Concurrency | At most 2 provider calls globally; one application process |
| Visitor capacity | At most 100 temporary sessions |
| Upload | 5 MiB; bounded extraction and normal format checks still apply |
| Course | At most 3 modules, 3 assignments, and 3 quizzes in the hosted demo |
| Retention | 24 hours; deletion and active-job cleanup behavior require acceptance tests |
| Demo end | `2026-12-16T08:00:00+00:00` — midnight PST at the end of December 15, after judging ends at noon |
| Host origin | Exact approved HTTPS origin; no wildcard origins |

Never put `NEBIUS_API_KEY` or the operator token in a browser, Git, image build arguments, logs, screenshots, or exports. Use the approved host's runtime secret environment. The separate judge access code is entered only into the HTTPS login form and private testing instructions; keep it out of Git, images, logs, screenshots, exports, and public guides. It is not a provider key or operator token.

Create private access values locally using [scripts/configure_judging.py](../../scripts/configure_judging.py):

```powershell
# Windows, from the repository root
.\.venv\Scripts\python.exe scripts/configure_judging.py
```

```sh
# macOS/Linux
.venv/bin/python scripts/configure_judging.py
```

The helper prompts for a hidden access code of at least 12 characters and confirmation, then writes its PBKDF2 hash and a random operator token to ignored `deploy/.env.judging.local`, with generation allowance zero. It refuses to overwrite an existing private file and does not configure a provider key or make an API request. Keep the plaintext code in an approved password manager for the private Devpost testing field. After approval, transfer the hash/operator token into the host's runtime secret settings using a trusted local editor or the host's secure interface; do not print the file into chat, screenshots, or logs.

For regular local Nebius BYO setup, [scripts/configure_nebius.py](../../scripts/configure_nebius.py) separately prompts for a masked key and saves it to ignored `.env.local`. Run it with the same Python executable as above. It preserves other configuration and makes no API request. Opening that prompt is approved; the developer enters the credential privately and never in chat. That development file is never copied into the judging deployment; configure its dedicated operator key directly in the approved host's secret environment.

The image builds the frontend in a separate Node stage and runs Python 3.12 as UID/GID 10001. It copies only named source directories/assets, not the whole workspace. Verify the mounted disk is writable as that user during the approved deployment; build-time ownership alone does not prove the actual host mount's permissions. The image intentionally omits optional OCR binaries. Readable PDF/DOCX/TXT uploads remain available; local installations retain optional OCR.

### Fly deployment gates

Fly CLI authentication and strict [configuration](../../deploy/fly.toml) validation have passed. Fly hosting/$15 are approved, with deployment conditional on final checks and complete live-test/content acceptance. No paid resources have been created. Authentication/configuration validation do not establish a running service or mounted-volume permissions. Remaining runtime credentials, new agreements, and payment/account steps stay owner-controlled. Once those private setup steps and conditional gates are satisfied:

1. Select the actual app name and HTTPS `fly.dev` origin, confirm the `iad` quote/capacity, and keep exactly one shared-CPU Machine and one 1 GB volume. Do not add an optional dedicated IP, domain, database, paid support, remote builder, or automatic disk growth.
2. Configure runtime secrets in the approved secure host flow. Keep the allowance at zero while checking storage and access controls. Do not put a secret in a shell command, TOML, build argument, transcript, or browser frontend.
3. Resolve mounted-volume ownership before opening access. The application must write as UID/GID 10001; an image's `chown` does not initialize a newly mounted block device. The official mount configuration documents no UID/GID option. The Fly bootstrap below remains unexecuted on Fly; the corresponding local Docker permission sequence passed. A Fly release command runs without mounted volumes, so it cannot perform this initialization. See the [configuration reference](https://docs.fly.io/reference/configuration) and [administrative console reference](https://docs.fly.io/flyctl/cmd/fly_ssh_console).
4. From the repository root, the deployment command is `fly deploy --config deploy/fly.toml --ha=false --local-only`. Its conditional approval takes effect **only after final checks and a passing live Nebius test**, with owner-controlled account setup complete. Local Docker builds avoid a remote build service; the deployment still pushes an image and creates billable runtime resources. Verify the actual Machine/volume/IP list and billing after deployment, rather than assuming the TOML limits Machine count.
5. Verify the real mounted disk survives restart, the host check passes, and a fresh browser completes the real approved Nebius workflow. Enable only the remaining approved inference amount after subtracting measured development charges. Confirm email failure and low-allowance delivery before offering the URL to judges.

**Proposed Fly mount bootstrap — not executed on Fly:** with CLI authentication complete, satisfy remaining private account/agreement steps and final acceptance gates, then make a temporary local configuration with the same `app` process group, VM shape, and volume. Override its command with `[processes] app = "/bin/sleep infinity"`, omit public services/HTTP checks, and keep the image's UID 10001. Deploy that temporary configuration with `--ha=false --local-only --no-public-ips`; then verify exactly one Machine and one intended volume. This is a billable deployment step, not a free local check.

Connect to that exact running Machine with `fly ssh console --machine ID --user root`. Verify `/var/lib/easy-street` is the dedicated mounted volume and contains no existing application data. Initialize only that directory, nonrecursively, to owner/group `10001:10001` and mode `0700`. Verify creation and removal of a temporary file after dropping all supplementary groups and switching to UID/GID 10001. Do not recursively change unrelated paths, use world-writable permissions, or run the web process as root. Finally deploy the normal configuration to the same default `app` process group and verify the application runs as UID 10001 with persistent writes. Fly documents that [process commands replace Docker CMD and subsequent deploys update existing same-group Machines](https://docs.fly.io/launch/processes). This sequence is based on documented capabilities; actual mounted-volume behavior still requires host acceptance.

The **local Docker rehearsal passed** using a uniquely named disposable volume with `volume-nocopy`: the mounted directory began empty and root-owned, and UID 10001 could not write. Administrative execution verified the exact mount, changed only its directory ownership/mode nonrecursively, and then UID 10001 created and removed a temporary file. The sleeping main process remained UID 10001 throughout. No ports were published, networking was disabled, no API key was supplied, and the disposable container/volume were removed and independently checked absent. This validates the local permission sequence, **not Fly platform acceptance**.

Fly's daily snapshots can retain deleted uploads for up to the configured five days. Disclose this host-level backup retention in the final privacy/testing instructions, verify the schedule, restrict account access, and remove retained data/snapshots when the approved retention period ends. Application deletion removes the active workspace but cannot erase an existing provider snapshot immediately. Restoring a snapshot can roll back accounting; reconcile later provider charges and uncertain reservations before reopening inference.

## Local container rehearsal

Rehearsal is independent of deployment. Use mock tests before any real provider test. Never insert an actual key into a copied shell command.

1. Run `scripts/configure_judging.py` with a test-only access code, or supply test-only access values through the local process environment. In the ignored `deploy/.env.judging.local` file, add `EASY_STREET_DEMO_ALLOW_HTTP=1` and `EASY_STREET_DEMO_ORIGIN=http://localhost:8000` for localhost rehearsal. Leave the generation allowance at zero and the provider key blank unless a specific paid test is approved. Readiness will correctly report unavailable when the provider key is absent.
2. From the repository root, validate without rendering secret values:

   ```sh
   docker compose --env-file deploy/.env.judging.local -f deploy/compose.judging.yaml config --quiet
   docker compose --env-file deploy/.env.judging.local -f deploy/compose.judging.yaml build
   docker compose --env-file deploy/.env.judging.local -f deploy/compose.judging.yaml up -d
   python scripts/demo_healthcheck.py --url http://127.0.0.1:8000
   ```

3. Test login, two independent visitors, upload, provider-unavailable behavior, export/deletion where available, restart persistence, and cleanup. The zero allowance must prevent paid calls. Use the separately approved live test to validate real generation.
4. Stop only the rehearsal service with `docker compose -f deploy/compose.judging.yaml down`. Preserve its volume until its accounting is reviewed. Do not remove or reset a live ledger to bypass a spending cutoff.

The diagnostic performs GET requests only. It does not invoke a model, retry, notify, or install a scheduled monitor. Avoid commands that print fully interpolated Compose configuration or container environments.

## Health, alerts, and actual monitoring state

**Monitoring is not configured and delivery has not been tested.** The owner approved free Render/Better Stack email monitoring, labeled failure/recovery test alerts, and the specific Better Stack free-account Terms/Privacy and sign-in email. Signup was confirmed and a magic link sent; the owner is completing sign-in privately. The approved monitor credential is the separate read-only operator token. Actual monitor configuration and delivery verification remain pending. Fly CLI authentication/configuration validation passed; paid resources and actual host acceptance remain pending. There is no native Fly billing-alert service to enable. Approval of Render email settings does not authorize an unrelated paid monitoring product. Do not claim coverage through judging before actual delivery is verified.

Prepared endpoints:

- `/health/live`: process liveness, no credentials or provider call.
- `/health/ready`: infrastructure readiness. It remains HTTP 200 when infrastructure works but generation is unavailable; `generation_available` must then be false. Restarting cannot repair an exhausted allowance.
- `/api/operator/status`: bearer-protected accounting/attention state without visitor content. It flags the final 20% of the application allowance, uncertain calls, recorded provider-stage failure, demo expiry, verified credit expiry within seven days, missing provider configuration, and cleanup failures. The persisted provider-health flag reflects observed calls, not a synthetic model request. It does not read the provider's real account balance or Fly bill. Use the separate read-only operator token.

Approved free scope, awaiting configuration and verification:

1. Complete the owner-controlled Better Stack magic-link sign-in. Its specific free-account Terms/Privacy and sign-in email were approved, and signup confirmation was observed; do not repeat signup or claim sign-in completion before confirmation. The [free personal tier](https://betterstack.com/pricing) includes ten monitors/heartbeats and email alerts; free checks have a [three-minute minimum interval](https://betterstack.com/docs/uptime/check-frequency/). Confirm the account stays free. No paid checks, SMS, calls, push integrations, or public status page are proposed. Other new host/service agreements remain private owner steps; Fly CLI authentication is already complete.
2. Configure two HTTPS **GET** checks, each every three minutes: `/health/ready` must return 2xx; `/api/operator/status` must contain the current compact JSON keyword `"needs_attention":false`. For the latter, set a private `Authorization: Bearer` header containing only the separate read-only operator token. Set TLS verification on, redirects off, email on, and SMS/call/push off. The [monitor API](https://betterstack.com/docs/uptime/api/create-a-new-monitor/) supports keyword checks and custom headers as an array of `{name,value}` objects; the [authentication documentation](https://betterstack.com/docs/uptime/request-parameters-headers-and-http-authentication/) confirms Bearer headers. Verify these settings on the actual free account before claiming coverage.
3. Better Stack must retain that read-only token in private monitor configuration; it must never receive the Nebius key or judge access code. Transfer it through a trusted private setup flow, never a URL/query string, plaintext command argument, Git, chat, screenshots, or response/configuration logs. A local runtime script can read secrets without printing them and return only monitor IDs. Do not dump API responses or screenshots containing configured headers.
4. Alert at **20% remaining of the enabled hosted allowance**, at **7 days before any verified credit expiry**, and on observed provider failures/other attention flags. At the current maximum $2.9928336 hosted allowance, the 20% threshold would be about $0.5986, reduced if further test charges lower the enabled limit. Reconcile the ledger and provider dashboard. A status-only HTTP check cannot detect low allowance, and no check here continuously invokes a model or verifies actual provider balance. Review host storage pressure and bills separately; the manual billing review route remains pending.
5. Use the owner's verified account email. For a labeled test, temporarily set the keyword monitor's required keyword to an impossible `TEST` value, wait for its incident email, then restore the expected keyword and wait for recovery. This changes only the monitor's test condition; it needs no inference request or application outage. Verify both messages with the owner, restore normal settings, and record monitor IDs, three-minute intervals, credential-free endpoint settings, test time, recipient confirmation, and escalation owner below. A delivery test does not replace verification of the real low-allowance/provider-failure condition using controlled test state.

The latest local backend/integration check reports **276 passed, 3 skipped in 35.58 seconds**, including mocked provider-health behavior. That is distinct from the two real runs and the ongoing owner content review. Neither result establishes a configured monitor or successful email delivery.

| Monitoring evidence | Actual state |
| --- | --- |
| Approved service/destination | Free Render/Better Stack email checks and labeled tests to verified account email approved; no paid service approved |
| Better Stack account access | Specific free Terms/Privacy/sign-in email approved; signup confirmed, owner magic-link sign-in pending |
| Fly native billing notifications | Unsupported by current official documentation; no automatic $15 cap established |
| External availability monitor | Not configured |
| Authenticated low-balance/expiry monitor | Not configured |
| Failure and recovery receipt | Not tested |
| On-call owner and response route | Owner confirmation pending |
| Manual Fly billing review and response route | Pending owner arrangement; no automated hosting-cost alert configured |

For a manual diagnostic after approval, set the operator token securely in the process environment and run:

```sh
python scripts/demo_healthcheck.py --url https://APPROVED-HOST --operator --expect-generation
```

The script prints booleans only, never tokens or response bodies. Exit 0 means its selected checks passed; 1 means attention; 2 means invalid local configuration. Running this command once is not ongoing monitoring.

## Emergency cutoff and recovery

The shared server allowance covers actual spend plus outstanding reservations and blocks new paid work at the cutoff. The initial $0 value intentionally blocks inference. Cancellation may not stop an in-flight request or its charge. Separate provider-account controls and usage reconciliation remain necessary.

**Reaching the cutoff interrupts live judging and requires intervention.** Before enabling the deployment, name an operator and a contact route in the private judging instructions. On an incident: inspect protected ledger and provider dashboard, preserve uncertain reservations, stop abusive access if present, and obtain approval for any additional funds. Raise the allowance only within the approved total. Restore availability, verify a fresh judge session, and confirm the alert recovery. Do not silently reset accounting or substitute a recording for a working service.

Keep adequate headroom before December 1. A judge should not need to pay, create a provider account, or wait for ordinary quota renewal. If the $0.50 temporary-session allowance or session capacity obstructs legitimate testing, the operator must provide a fresh testing session or approved adjustment promptly.

After judging ends, obtain the owner's direction to stop hosting and revoke the dedicated key. The application's expiry stops generation; it does not cancel host billing. Clean up temporary data and snapshots according to the final approved privacy policy. Retain non-content accounting evidence needed for reconciliation.
