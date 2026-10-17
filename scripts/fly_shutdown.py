"""Date-gated retirement of ONE approved Fly judging deployment.

No provider requests, visitor backups, arbitrary commands, target arguments or
automatic HTTP retries. GitHub supplies scheduling, serialization and alerts.
An encrypted aggregate backup must be uploaded and verified before deletion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import ipaddress
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

APP = "easy-street-agammann-2026"
APP_ID = "vxemq2v6w6z59gz6"
MACHINE = "862ee1ce470678"
VOLUME = "vol_r1jgw2pgpx36ne9r"
REPOSITORY = "agammann/easy-street"
SNAPSHOTS_DUE = datetime(2026, 12, 9, 20, 30, tzinfo=timezone.utc)
SHUTDOWN_DUE = datetime(2026, 12, 15, 20, 30, tzinfo=timezone.utc)
API = "https://api.machines.dev/v1"
MAX_RESPONSE = 1024 * 1024

# Fixed command: read only the operator ledger and a non-secret allowance flag.
# A SQLite backup to memory gives one consistent snapshot without copying WAL
# files or creating a persisted copy containing pseudonymous session identifiers.
AGGREGATE_COMMAND = """import json, math, os, sqlite3
source = sqlite3.connect('file:/var/lib/easy-street/operator-usage.sqlite3?mode=ro', uri=True, timeout=20)
memory = sqlite3.connect(':memory:')
source.backup(memory)
source.close()
assert memory.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
memory.execute('PRAGMA query_only=ON')
rows = memory.execute('SELECT model,stage,state,COUNT(*),SUM(input_tokens),SUM(output_tokens),SUM(actual),SUM(reserved) FROM calls GROUP BY model,stage,state ORDER BY model,stage,state').fetchall()
health = memory.execute('SELECT stage,state FROM provider_health ORDER BY stage').fetchall()
allowance = float(os.environ.get('EASY_STREET_DEMO_BUDGET_USD', 'nan'))
print(json.dumps({'schema':1,'paused':math.isfinite(allowance) and allowance == 0,'calls':rows,'health':health}, separators=(',',':'), allow_nan=False))
memory.close()
"""


class ShutdownError(RuntimeError):
    """Only fixed, non-sensitive messages may cross the CLI boundary."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ShutdownError("A timestamp was malformed.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ShutdownError("A timestamp lacked its UTC offset.")
    return parsed.astimezone(timezone.utc)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Http:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())

    def raw(self, method, url, token=None, body=None, redirect=False):
        headers = {"User-Agent": "EasyStreet-shutdown", "Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, method=method, headers=headers,
                                     data=canonical(body) if body is not None else None)
        try:
            with self.opener.open(req, timeout=40) as response:
                data = response.read(MAX_RESPONSE + 1)
                if len(data) > MAX_RESPONSE:
                    raise ShutdownError("A remote response exceeded the safe size limit.")
                return response.status, dict(response.headers), data
        except urllib.error.HTTPError as error:
            if redirect and error.code == 302:
                return 302, dict(error.headers), b""
            safe_error = ShutdownError("A remote request failed; absence was not assumed.")
            safe_error.status = error.code
            raise safe_error from None
        except (OSError, ValueError):
            raise ShutdownError("A remote request could not be completed safely.") from None

    def json(self, method, url, token, body=None):
        _, _, raw = self.raw(method, url, token, body)
        try:
            return json.loads(raw) if raw else None
        except (ValueError, UnicodeError):
            raise ShutdownError("A remote response was not valid JSON.") from None


class Fly:
    def __init__(self, token, http=None):
        if not token or "\n" in token or "\r" in token:
            raise ShutdownError("Configure the app-scoped Fly runtime credential.")
        self.token, self.http = token, http or Http()

    def request(self, method, suffix="", body=None):
        # Never accept an arbitrary host, app, traversal or query from callers.
        if ".." in suffix or "?" in suffix or (suffix and not suffix.startswith("/")):
            raise ShutdownError("Invalid fixed-app operation.")
        return self.http.json(method, API + "/apps/" + APP + suffix, self.token, body)


def inventory(fly):
    app = fly.request("GET")
    machines = fly.request("GET", "/machines")
    volumes = fly.request("GET", "/volumes")
    assignments = fly.request("GET", "/ip_assignments")
    if not isinstance(app, dict) or app.get("name") != APP or app.get("id") != APP_ID:
        raise ShutdownError("The approved app identity could not be verified.")
    if not isinstance(machines, list) or not isinstance(volumes, list) or not isinstance(assignments, dict) or not isinstance(assignments.get("ips"), list):
        raise ShutdownError("The resource inventory was malformed.")
    if len(machines) > 1 or any(not isinstance(m, dict) or m.get("id") != MACHINE for m in machines):
        raise ShutdownError("Unexpected Machine inventory; no resources were changed.")
    if len(volumes) > 1 or any(not isinstance(v, dict) or v.get("id") != VOLUME for v in volumes):
        raise ShutdownError("Unexpected volume inventory; no resources were changed.")
    for machine in machines:
        cfg = machine.get("config", {})
        guest = cfg.get("guest", {})
        if machine.get("region") != "iad" or guest.get("cpu_kind") != "shared" or guest.get("cpus") != 1 or guest.get("memory_mb") != 512:
            raise ShutdownError("The approved Machine configuration changed.")
        mounts = cfg.get("mounts", [])
        if len(mounts) != 1 or mounts[0].get("volume") != VOLUME or mounts[0].get("path") != "/var/lib/easy-street":
            raise ShutdownError("The approved mounted volume could not be verified.")
    for volume in volumes:
        if volume.get("region") != "iad" or volume.get("size_gb") != 1 or volume.get("attached_machine_id") not in (None, "", MACHINE):
            raise ShutdownError("The approved volume configuration changed.")
    ips = []
    for value in assignments["ips"]:
        try:
            address = ipaddress.ip_address(value["ip"])
        except (KeyError, TypeError, ValueError):
            raise ShutdownError("The IP inventory was malformed.") from None
        if value.get("egress") is not False or (address.version == 4 and value.get("shared") is not True) or address.is_private:
            raise ShutdownError("Unexpected paid/private IP allocation; no resources were changed.")
        ips.append(str(address))
    if len(ips) > 2 or len(set(ips)) != len(ips):
        raise ShutdownError("Unexpected IP allocation count.")
    try:
        snapshots = fly.request("GET", "/volumes/" + VOLUME + "/snapshots")
    except ShutdownError as error:
        if not volumes and getattr(error, "status", None) == 404:
            snapshots = None  # Unknown, never silently interpreted as zero.
        else:
            raise
    if snapshots is not None:
        if not isinstance(snapshots, list) or len(snapshots) > 100:
            raise ShutdownError("Snapshot inventory could not be verified.")
        safe_snapshots = []
        for snapshot in snapshots:
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("id"), str) or not snapshot["id"] or type(snapshot.get("retention_days")) is not int or not 1 <= snapshot["retention_days"] <= 60:
                raise ShutdownError("Snapshot metadata could not be verified.")
            timestamp(snapshot["created_at"])
            safe_snapshots.append({k: snapshot[k] for k in ("id", "created_at", "retention_days")})
        snapshots = safe_snapshots
    return {"app_id": app["id"], "machines": machines, "volumes": volumes,
            "ips": sorted(ips), "snapshots": snapshots}


def identity(inv):
    return {"app": APP, "app_id": inv["app_id"], "machine": MACHINE, "volume": VOLUME,
            "ips": inv["ips"]}


def aggregate(fly):
    response = fly.request("POST", "/machines/" + MACHINE + "/exec",
                           {"cmd": shlex.join(["python", "-c", AGGREGATE_COMMAND]), "timeout": 30})
    if not isinstance(response, dict) or response.get("exit_code") != 0 or response.get("exit_signal", 0) != 0 or response.get("stderr"):
        raise ShutdownError("The consistent aggregate ledger backup failed.")
    try:
        value = json.loads(response["stdout"])
        if set(value) != {"schema", "paused", "calls", "health"} or value["schema"] != 1 or type(value["paused"]) is not bool:
            raise ValueError()
        if not isinstance(value["calls"], list) or len(value["calls"]) > 8 or not isinstance(value["health"], list) or len(value["health"]) > 2:
            raise ValueError()
        for row in value["calls"]:
            if not isinstance(row, list) or len(row) != 8 or row[0] != "nvidia/nemotron-3-super-120b-a12b" or row[1] not in ("generation", "verification") or row[2] not in ("completed", "rejected", "uncertain", "in_flight"):
                raise ValueError()
            if any(type(number) is not int or number < 0 for number in row[3:6]):
                raise ValueError()
            if any(type(number) not in (int, float) or not math.isfinite(number) or number < 0 for number in row[6:]):
                raise ValueError()
        for row in value["health"]:
            if not isinstance(row, list) or len(row) != 2 or row[0] not in ("generation", "verification") or row[1] not in ("healthy", "failing"):
                raise ValueError()
        return value
    except (ValueError, KeyError, TypeError):
        raise ShutdownError("The aggregate ledger did not match its privacy schema.") from None


def certificate_bytes(path):
    raw = Path(path).read_bytes()
    if len(raw) > 65536 or b"PRIVATE KEY" in raw or b"BEGIN CERTIFICATE" not in raw:
        raise ShutdownError("Supply only the owner's public encryption certificate.")
    return raw


def prepare_backup(fly, directory, certificate, now, run_id, encrypt=None, rehearsal=False):
    if not rehearsal and now < SHUTDOWN_DUE:
        raise ShutdownError("A final backup is prohibited before the shutdown date; use rehearsal-backup.")
    inv = inventory(fly)
    if len(inv["machines"]) != 1 or len(inv["volumes"]) != 1 or inv["machines"][0].get("state") != "started":
        raise ShutdownError("A running original Machine and volume are required for backup.")
    value = aggregate(fly)
    in_flight = sum(row[3] for row in value["calls"] if row[2] == "in_flight")
    if not rehearsal and (value["paused"] is not True or in_flight):
        raise ShutdownError("Pause inference and settle active calls before the final backup.")
    cert = certificate_bytes(certificate)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cipher = directory / "ledger.cms"
    receipt_path = directory / "receipt.json"
    if cipher.exists() or receipt_path.exists():
        raise ShutdownError("Refusing to overwrite an existing backup or receipt.")
    if not run_id.isdecimal() or len(run_id) > 25:
        raise ShutdownError("A valid GitHub run identifier is required.")
    if encrypt is None:
        def encrypt(data):
            try:
                result = subprocess.run(["openssl", "cms", "-encrypt", "-aes256", "-binary", "-outform", "DER", str(certificate)],
                                        input=data, capture_output=True, timeout=30, check=True)
                return result.stdout
            except (OSError, subprocess.SubprocessError):
                raise ShutdownError("Public-certificate encryption failed.") from None
    encrypted = encrypt(canonical(value))
    if not isinstance(encrypted, bytes) or len(encrypted) < 32 or len(encrypted) > MAX_RESPONSE or encrypted.startswith(b"{"):
        raise ShutdownError("The encrypted backup was invalid.")
    receipt = {"schema": 1, "identity": identity(inv), "created_at": now.isoformat(), "run_id": run_id, "rehearsal": rehearsal,
               "ciphertext_sha256": digest(encrypted), "certificate_sha256": digest(cert),
               "aggregate_sha256": digest(canonical(value)), "paused": value["paused"],
               "in_flight": in_flight, "snapshot_inventory": inv["snapshots"],
               "snapshots_disabled": inv["volumes"][0].get("auto_backup_enabled") is False}
    # Aggregate plaintext exists only in memory and OpenSSL's stdin.
    with cipher.open("xb") as output:
        output.write(encrypted)
    with receipt_path.open("xb") as output:
        output.write(canonical(receipt))
    return {"status": "encrypted_backup_prepared", "paused": receipt["paused"], "in_flight": receipt["in_flight"]}


def downloaded_backup(http, artifact_id, token, expected_digest=None):
    if not artifact_id.isdecimal() or not token:
        raise ShutdownError("An authenticated artifact reference is required.")
    endpoint = "https://api.github.com/repos/" + REPOSITORY + "/actions/artifacts/" + artifact_id
    metadata = http.json("GET", endpoint, token)
    actual_digest = metadata.get("digest", "") if isinstance(metadata, dict) else ""
    if (not isinstance(metadata, dict) or str(metadata.get("id")) != artifact_id
            or metadata.get("workflow_run", {}).get("head_branch") != "main"
            or metadata.get("expired") is not False or not metadata.get("name", "").startswith("easy-street-shutdown-ledger-")
            or not isinstance(actual_digest, str) or not actual_digest.startswith("sha256:") or len(actual_digest) != 71
            or (expected_digest is not None and actual_digest != expected_digest)):
        raise ShutdownError("The uploaded artifact could not be verified.")
    status, headers, _ = http.raw("GET", endpoint + "/zip", token, redirect=True)
    location = headers.get("Location", headers.get("location", ""))
    parsed = urllib.parse.urlsplit(location)
    if status != 302 or parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname or not parsed.hostname.endswith((".blob.core.windows.net", ".actions.githubusercontent.com")):
        raise ShutdownError("The artifact download location was not trusted.")
    # Signed storage URL receives NO GitHub/Fly credential; never log its query.
    _, _, archived = http.raw("GET", location)
    if "sha256:" + digest(archived) != actual_digest:
        raise ShutdownError("The uploaded artifact digest did not match.")
    try:
        with zipfile.ZipFile(io.BytesIO(archived)) as archive:
            entries = archive.infolist()
            if sorted(e.filename for e in entries) != ["ledger.cms", "receipt.json"] or sum(e.file_size for e in entries) > MAX_RESPONSE:
                raise ValueError()
            cipher, receipt_raw = archive.read("ledger.cms"), archive.read("receipt.json")
    except (ValueError, KeyError, OSError, zipfile.BadZipFile):
        raise ShutdownError("The artifact does not contain the exact encrypted backup.") from None
    return metadata, cipher, receipt_raw


def check_backup_files(cipher, receipt_raw, certificate):
    receipt = json.loads(receipt_raw)
    if (len(receipt_raw) > 16384 or len(cipher) > MAX_RESPONSE or not isinstance(receipt, dict)
            or receipt.get("schema") != 1 or receipt.get("ciphertext_sha256") != digest(cipher)
            or receipt.get("certificate_sha256") != digest(certificate_bytes(certificate))):
        raise ShutdownError("The backup files do not match their receipt.")
    return receipt


def artifact_context(env):
    if env.get("GITHUB_REPOSITORY") != REPOSITORY or env.get("GITHUB_REF") != "refs/heads/main" or not env.get("GITHUB_TOKEN"):
        raise ShutdownError("Verified default-branch artifact context is required.")


def verify_uploaded_backup(http, directory, certificate, env):
    artifact_context(env)
    directory = Path(directory)
    receipt_raw, cipher = (directory / "receipt.json").read_bytes(), (directory / "ledger.cms").read_bytes()
    receipt = check_backup_files(cipher, receipt_raw, certificate)
    metadata, stored_cipher, stored_receipt = downloaded_backup(http, env.get("EASY_STREET_SHUTDOWN_ARTIFACT_ID", ""),
        env["GITHUB_TOKEN"], env.get("EASY_STREET_SHUTDOWN_ARTIFACT_DIGEST", ""))
    if stored_cipher != cipher or stored_receipt != receipt_raw or str(metadata["workflow_run"].get("id")) != receipt.get("run_id"):
        raise ShutdownError("The uploaded artifact differs from the prepared backup.")
    return receipt


def recover_backup(http, directory, certificate, now, env):
    artifact_context(env)
    if now < SHUTDOWN_DUE:
        raise ShutdownError("Final backup recovery is prohibited before retirement.")
    listing = http.json("GET", "https://api.github.com/repos/" + REPOSITORY + "/actions/artifacts?per_page=100", env["GITHUB_TOKEN"])
    if not isinstance(listing, dict) or not isinstance(listing.get("artifacts"), list):
        raise ShutdownError("Backup artifact inventory was malformed.")
    candidates = [a for a in listing["artifacts"] if isinstance(a, dict) and a.get("expired") is False
                  and a.get("name", "").startswith("easy-street-shutdown-ledger-")
                  and a.get("workflow_run", {}).get("head_branch") == "main"]
    if not candidates:
        raise ShutdownError("No final backup artifact is available for recovery.")
    candidate = max(candidates, key=lambda a: timestamp(a["created_at"]))
    metadata, cipher, receipt_raw = downloaded_backup(http, str(candidate["id"]), env["GITHUB_TOKEN"])
    receipt = check_backup_files(cipher, receipt_raw, certificate)
    age = (now - timestamp(receipt["created_at"])).total_seconds()
    if (receipt.get("rehearsal") is not False or receipt.get("paused") is not True or receipt.get("in_flight") != 0
            or not 0 <= age <= 7 * 86400 or timestamp(receipt["created_at"]) < SHUTDOWN_DUE
            or receipt.get("identity", {}).get("app_id") != APP_ID
            or str(metadata["workflow_run"].get("id")) != receipt.get("run_id")):
        raise ShutdownError("The recovered artifact is not an eligible final backup.")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in (("ledger.cms", cipher), ("receipt.json", receipt_raw)):
        with (directory / name).open("xb") as output:
            output.write(data)
    return {"status": "final_backup_recovered", "artifact_id": str(metadata["id"]), "artifact_digest": metadata["digest"]}


def wait_for(fly, predicate, message, sleep=time.sleep):
    for attempt in range(31):
        inv = inventory(fly)
        if predicate(inv):
            return inv
        if attempt < 30:
            sleep(1)
    raise ShutdownError(message)


def disable_snapshots(fly, now):
    if now < SNAPSHOTS_DUE:
        raise ShutdownError("Snapshot changes are prohibited before December 9, 20:30 UTC.")
    inv = inventory(fly)
    if not inv["volumes"]:
        return {"status": "no_active_volume", "remaining_snapshots": len(inv["snapshots"]) if inv["snapshots"] is not None else None,
                "snapshot_inventory_available": inv["snapshots"] is not None}
    if inv["volumes"] and inv["volumes"][0].get("auto_backup_enabled") is not False:
        fly.request("PUT", "/volumes/" + VOLUME, {"auto_backup_enabled": False})
    checked = inventory(fly)
    if checked["volumes"] and checked["volumes"][0].get("auto_backup_enabled") is not False:
        raise ShutdownError("Disabling future snapshots was not confirmed.")
    return {"status": "future_snapshots_disabled", "remaining_snapshots": len(checked["snapshots"]) if checked["snapshots"] is not None else None}


def execute(fly, directory, certificate, now, env, http=None):
    if now < SHUTDOWN_DUE:
        raise ShutdownError("Destructive shutdown is prohibited before December 15, 20:30 UTC.")
    receipt = verify_uploaded_backup(http or Http(), directory, certificate, env)
    age = (now - timestamp(receipt["created_at"])).total_seconds()
    if not 0 <= age <= 7 * 86400 or timestamp(receipt["created_at"]) < SHUTDOWN_DUE or receipt.get("rehearsal") is not False or receipt.get("paused") is not True or receipt.get("in_flight") != 0:
        raise ShutdownError("A fresh, paused, quiescent final backup is required.")
    inv = inventory(fly)
    recorded = receipt.get("identity", {})
    if {**identity(inv), "ips": recorded.get("ips")} != recorded or not set(inv["ips"]).issubset(recorded.get("ips", [])):
        raise ShutdownError("The resource identity changed since backup.")
    empty_before_delete = (receipt.get("snapshots_disabled") is True and receipt.get("snapshot_inventory") == []
                           and not inv["snapshots"] and (not inv["volumes"] or inv["volumes"][0].get("auto_backup_enabled") is False))
    # Retained snapshots must not keep avoidable compute/disk billing running.
    # They still prevent a final zero-storage claim until separately verified.
    if inv["machines"]:
        machine = inv["machines"][0]
        if machine.get("state") == "started":
            current = aggregate(fly)
            if current["paused"] is not True or digest(canonical(current)) != receipt["aggregate_sha256"]:
                raise ShutdownError("The paused ledger changed after backup; preserve it before deletion.")
            fly.request("POST", "/machines/" + MACHINE + "/stop", {"signal": "SIGTERM", "timeout": "30s"})
            wait_for(fly, lambda i: not i["machines"] or i["machines"][0].get("state") == "stopped", "The Machine did not stop within the bounded wait.")
        fly.request("DELETE", "/machines/" + MACHINE)
    checked = wait_for(fly, lambda i: not i["machines"] and (not i["volumes"] or not i["volumes"][0].get("attached_machine_id")), "Machine deletion/detachment was not confirmed.")
    if checked["volumes"]:
        if checked["volumes"][0].get("attached_machine_id"):
            raise ShutdownError("The volume remains attached; no volume was deleted.")
        fly.request("DELETE", "/volumes/" + VOLUME)
    for address in inv["ips"]:
        fly.request("DELETE", "/ip_assignments/" + urllib.parse.quote(address, safe=""))
    final = wait_for(fly, lambda i: not i["machines"] and not i["volumes"] and not i["ips"], "Retirement did not finish within the bounded wait.")
    if final["machines"] or final["volumes"] or final["ips"] or final["snapshots"]:
        raise ShutdownError("Retirement is incomplete; resources or snapshots remain.")
    proof = "current_api_inventory"
    if final["snapshots"] is None:
        if not empty_before_delete:
            raise ShutdownError("Compute, volume and IPs are gone; snapshot storage remains unverified.")
        proof = "verified_empty_before_delete"
    return {"status": "retired", "machines": 0, "volumes": 0, "ips": 0, "snapshots": 0,
            "snapshot_proof": proof, "app_name_retained": True, "notice": "Earlier usage can appear on a later invoice."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inventory", "disable-snapshots", "prepare-backup", "rehearsal-backup", "recover-backup", "execute"), default="inventory")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--certificate", type=Path)
    args = parser.parse_args(argv)
    try:
        now = datetime.now(timezone.utc)
        fly = Fly(os.environ.get("FLY_API_TOKEN", ""))
        if args.mode == "inventory":
            inv = inventory(fly)
            result = {"status": "inventory_only", "machines": len(inv["machines"]), "volumes": len(inv["volumes"]),
                      "machine_started": bool(inv["machines"] and inv["machines"][0].get("state") == "started"),
                      "ips": len(inv["ips"]), "snapshots": len(inv["snapshots"]) if inv["snapshots"] is not None else None,
                      "snapshot_inventory_available": inv["snapshots"] is not None,
                      "snapshot_change_due": now >= SNAPSHOTS_DUE, "shutdown_due": now >= SHUTDOWN_DUE}
        elif args.mode == "disable-snapshots":
            result = disable_snapshots(fly, now)
        else:
            if args.backup_dir is None or args.certificate is None:
                raise ShutdownError("Backup directory and public certificate are required.")
            if args.mode in ("prepare-backup", "rehearsal-backup"):
                result = prepare_backup(fly, args.backup_dir, args.certificate, now, os.environ.get("GITHUB_RUN_ID", ""), rehearsal=args.mode == "rehearsal-backup")
            elif args.mode == "recover-backup":
                result = recover_backup(Http(), args.backup_dir, args.certificate, now, os.environ)
            else:
                result = execute(fly, args.backup_dir, args.certificate, now, os.environ)
        print(json.dumps(result, sort_keys=True))
        return 0
    except ShutdownError as error:
        print(json.dumps({"status": "attention", "detail": str(error)}))
        return 1
    except Exception:
        print(json.dumps({"status": "attention", "detail": "Shutdown verification failed safely; inspect the private operator configuration."}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
