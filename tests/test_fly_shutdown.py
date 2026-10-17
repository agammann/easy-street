"""Retirement safeguards with mocked Fly/GitHub APIs; no network or inference."""
import copy
from datetime import timedelta
import io
import json
import sqlite3
import zipfile

import pytest

from scripts import fly_shutdown as shutdown


class FlyFixture:
    def __init__(self):
        self.calls = []
        self.machine = {"id": shutdown.MACHINE, "region": "iad", "state": "started", "config": {
            "guest": {"cpu_kind": "shared", "cpus": 1, "memory_mb": 512},
            "mounts": [{"volume": shutdown.VOLUME, "path": "/var/lib/easy-street"}]}}
        self.volume = {"id": shutdown.VOLUME, "region": "iad", "size_gb": 1,
                       "attached_machine_id": shutdown.MACHINE, "auto_backup_enabled": False}
        self.ips = [{"ip": "66.241.124.22", "shared": True, "egress": False}]
        self.snapshots = []
        self.app = {"name": shutdown.APP, "id": shutdown.APP_ID}
        self.ledger = {"schema": 1, "paused": True, "calls": [
            ["nvidia/nemotron-3-super-120b-a12b", "generation", "completed", 1, 2263, 1529, .002055, 0],
            ["nvidia/nemotron-3-super-120b-a12b", "verification", "completed", 1, 4606, 997, .0022791, 0]],
            "health": [["generation", "healthy"], ["verification", "healthy"]]}
        self.fail_delete_volume = False
        self.fail_snapshot_listing = False

    def request(self, method, suffix="", body=None):
        self.calls.append((method, suffix, copy.deepcopy(body)))
        if method == "GET":
            if suffix == "":
                return copy.deepcopy(self.app)
            if suffix == "/machines":
                return copy.deepcopy([self.machine] if self.machine else [])
            if suffix == "/volumes":
                return copy.deepcopy([self.volume] if self.volume else [])
            if suffix == "/ip_assignments":
                return copy.deepcopy({"ips": self.ips})
            if suffix.endswith("/snapshots"):
                if self.fail_snapshot_listing:
                    raise shutdown.ShutdownError("Snapshot list failed.")
                return copy.deepcopy(self.snapshots)
        if method == "POST" and suffix.endswith("/exec"):
            assert body["timeout"] == 30
            assert "operator-usage.sqlite3?mode=ro" in body["cmd"]
            assert "NEBIUS_API_KEY" not in body["cmd"]
            return {"exit_code": 0, "exit_signal": 0, "stderr": "", "stdout": json.dumps(self.ledger)}
        if method == "PUT" and suffix == "/volumes/" + shutdown.VOLUME:
            assert body == {"auto_backup_enabled": False}
            self.volume["auto_backup_enabled"] = False
            return copy.deepcopy(self.volume)
        if method == "POST" and suffix.endswith("/stop"):
            self.machine["state"] = "stopped"
            return None
        if method == "DELETE" and suffix == "/machines/" + shutdown.MACHINE:
            self.machine = None
            self.volume["attached_machine_id"] = None
            return None
        if method == "DELETE" and suffix == "/volumes/" + shutdown.VOLUME:
            if self.fail_delete_volume:
                raise shutdown.ShutdownError("Volume deletion failed.")
            self.volume = None
            return None
        if method == "DELETE" and suffix.startswith("/ip_assignments/"):
            self.ips = []
            return None
        raise AssertionError((method, suffix, body))


class ArtifactFixture:
    def __init__(self, directory):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in ("ledger.cms", "receipt.json"):
                archive.writestr(name, (directory / name).read_bytes())
        self.archive = out.getvalue()
        self.metadata = {"id": 321, "name": "easy-street-shutdown-ledger-100", "expired": False,
                         "created_at": shutdown.SHUTDOWN_DUE.isoformat(),
                         "digest": "sha256:" + shutdown.digest(self.archive),
                         "workflow_run": {"id": 100, "head_branch": "main"}}
        self.redirect = "https://test.blob.core.windows.net/archive?private-signed-query"
        self.calls = []

    def json(self, method, url, token, body=None):
        self.calls.append((method, url, token))
        assert method == "GET"
        assert url.startswith("https://api.github.com/repos/" + shutdown.REPOSITORY)
        if "?per_page" in url:
            return {"artifacts": [copy.deepcopy(self.metadata)]}
        return copy.deepcopy(self.metadata)

    def raw(self, method, url, token=None, body=None, redirect=False):
        self.calls.append((method, url, token))
        if url.endswith("/zip"):
            return 302, {"Location": self.redirect}, b""
        assert token is None  # Never forward either provider credential to storage.
        assert url == self.redirect
        return 200, {}, self.archive


@pytest.fixture
def prepared(tmp_path):
    fly = FlyFixture()
    certificate = tmp_path / "public.pem"
    certificate.write_text("-----BEGIN CERTIFICATE-----\npublic-test-recipient\n-----END CERTIFICATE-----\n")
    directory = tmp_path / "prepared"
    shutdown.prepare_backup(fly, directory, certificate, shutdown.SHUTDOWN_DUE, "100",
                            encrypt=lambda data: b"opaque-encrypted-ledger-fixture" * 3)
    artifacts = ArtifactFixture(directory)
    env = {"GITHUB_REPOSITORY": shutdown.REPOSITORY, "GITHUB_REF": "refs/heads/main", "GITHUB_RUN_ID": "200",
           "GITHUB_TOKEN": "private-github-test-token", "EASY_STREET_SHUTDOWN_ARTIFACT_ID": "321",
           "EASY_STREET_SHUTDOWN_ARTIFACT_DIGEST": artifacts.metadata["digest"]}
    fly.calls.clear()
    return fly, directory, certificate, artifacts, env


def writes(fly):
    return [call for call in fly.calls if call[0] != "GET"]


def test_early_shutdown_and_snapshot_changes_cannot_mutate(prepared):
    fly, directory, certificate, artifacts, env = prepared
    with pytest.raises(shutdown.ShutdownError, match="prohibited"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE - timedelta(seconds=1), env, artifacts)
    with pytest.raises(shutdown.ShutdownError, match="prohibited"):
        shutdown.disable_snapshots(fly, shutdown.SNAPSHOTS_DUE - timedelta(seconds=1))
    assert fly.calls == artifacts.calls == []


@pytest.mark.parametrize("change", ["app", "machine", "volume", "mount", "paid_ip", "memory"])
def test_unexpected_resources_are_not_deleted(prepared, change):
    fly, directory, certificate, artifacts, env = prepared
    if change == "app":
        fly.app["id"] = "replacement-app"
    elif change == "machine":
        fly.machine["id"] = "different-machine"
    elif change == "volume":
        fly.volume["id"] = "different-volume"
    elif change == "mount":
        fly.machine["config"]["mounts"][0]["path"] = "/other"
    elif change == "paid_ip":
        fly.ips[0]["shared"] = False
    else:
        fly.machine["config"]["guest"]["memory_mb"] = 1024
    with pytest.raises(shutdown.ShutdownError):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert not writes(fly)


def test_due_snapshot_change_only_disables_future_backups(prepared):
    fly, *_ = prepared
    fly.volume["auto_backup_enabled"] = True
    fly.snapshots = [{"id": "existing-snapshot", "created_at": shutdown.SNAPSHOTS_DUE.isoformat(), "retention_days": 5}]
    value = shutdown.disable_snapshots(fly, shutdown.SNAPSHOTS_DUE)
    assert value["remaining_snapshots"] == 1
    assert writes(fly) == [("PUT", "/volumes/" + shutdown.VOLUME, {"auto_backup_enabled": False})]


def test_backup_is_aggregate_only_and_has_no_plaintext_file(prepared):
    fly, directory, *_ = prepared
    assert sorted(p.name for p in directory.iterdir()) == ["ledger.cms", "receipt.json"]
    assert b"2263" not in (directory / "ledger.cms").read_bytes()
    receipt = json.loads((directory / "receipt.json").read_bytes())
    assert "calls" not in receipt and "health" not in receipt
    assert "visitors" not in shutdown.AGGREGATE_COMMAND
    assert "session_id" not in shutdown.AGGREGATE_COMMAND
    assert "NEBIUS_API_KEY" not in shutdown.AGGREGATE_COMMAND


def test_rehearsal_cannot_be_used_for_final_deletion(tmp_path):
    fly = FlyFixture()
    fly.ledger["paused"] = False
    cert = tmp_path / "public.pem"
    cert.write_text("-----BEGIN CERTIFICATE-----\npublic\n-----END CERTIFICATE-----")
    directory = tmp_path / "rehearsal"
    shutdown.prepare_backup(fly, directory, cert, shutdown.SHUTDOWN_DUE, "100", rehearsal=True,
                            encrypt=lambda data: b"opaque" * 20)
    artifacts = ArtifactFixture(directory)
    env = {"GITHUB_REPOSITORY": shutdown.REPOSITORY, "GITHUB_REF": "refs/heads/main", "GITHUB_TOKEN": "fixture",
           "EASY_STREET_SHUTDOWN_ARTIFACT_ID": "321", "EASY_STREET_SHUTDOWN_ARTIFACT_DIGEST": artifacts.metadata["digest"]}
    fly.calls.clear()
    with pytest.raises(shutdown.ShutdownError, match="quiescent"):
        shutdown.execute(fly, directory, cert, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert not writes(fly)


@pytest.mark.parametrize("case", ["unpaused", "in_flight", "stale", "changed"])
def test_final_cleanup_requires_quiescence_unchanged_ledger_and_no_snapshots(prepared, case):
    fly, directory, certificate, artifacts, env = prepared
    now = shutdown.SHUTDOWN_DUE
    if case == "unpaused":
        fly.ledger["paused"] = False
    elif case == "in_flight":
        fly.ledger["calls"][0][2] = "in_flight"
    elif case == "stale":
        now += timedelta(days=8)
    elif case == "changed":
        fly.ledger["calls"][0][6] += .01
    with pytest.raises(shutdown.ShutdownError):
        shutdown.execute(fly, directory, certificate, now, env, artifacts)
    assert not [call for call in writes(fly) if not call[1].endswith("/exec")]


def test_retained_snapshots_do_not_keep_compute_billing_running(prepared):
    fly, directory, certificate, artifacts, env = prepared
    fly.snapshots = [{"id": "retained", "created_at": shutdown.SHUTDOWN_DUE.isoformat(), "retention_days": 5}]
    with pytest.raises(shutdown.ShutdownError, match="snapshots remain"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert fly.machine is None and fly.volume is None and fly.ips == []


def test_deleted_volume_404_requires_verified_predelete_snapshot_evidence(prepared):
    fly, directory, certificate, artifacts, env = prepared
    original = fly.request
    def request(method, suffix="", body=None):
        if suffix.endswith("/snapshots") and fly.volume is None:
            error = shutdown.ShutdownError("A remote request failed; absence was not assumed.")
            error.status = 404
            raise error
        return original(method, suffix, body)
    fly.request = request
    result = shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert result["status"] == "retired" and result["snapshot_proof"] == "verified_empty_before_delete"
    assert shutdown.inventory(fly)["snapshots"] is None


def test_deleted_volume_404_is_unknown_without_disabled_empty_snapshot_receipt(prepared):
    fly, directory, certificate, _, env = prepared
    receipt_path = directory / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["snapshots_disabled"] = False
    receipt_path.write_bytes(shutdown.canonical(receipt))
    artifacts = ArtifactFixture(directory)
    env["EASY_STREET_SHUTDOWN_ARTIFACT_DIGEST"] = artifacts.metadata["digest"]
    original = fly.request
    def request(method, suffix="", body=None):
        if suffix.endswith("/snapshots") and fly.volume is None:
            error = shutdown.ShutdownError("No snapshot inventory is available.")
            error.status = 404
            raise error
        return original(method, suffix, body)
    fly.request = request
    with pytest.raises(shutdown.ShutdownError, match="snapshot storage remains unverified"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert fly.machine is None and fly.volume is None and fly.ips == []


@pytest.mark.parametrize("case", ["fork", "wrong_run", "expired", "digest", "redirect", "tamper", "missing_context"])
def test_artifact_proof_cannot_be_faked_or_forward_credentials(prepared, case):
    fly, directory, certificate, artifacts, env = prepared
    if case == "fork":
        artifacts.metadata["workflow_run"]["head_branch"] = "other"
    elif case == "wrong_run":
        artifacts.metadata["workflow_run"]["id"] = 999
    elif case == "expired":
        artifacts.metadata["expired"] = True
    elif case == "digest":
        env["EASY_STREET_SHUTDOWN_ARTIFACT_DIGEST"] = "sha256:" + "0" * 64
    elif case == "redirect":
        artifacts.redirect = "https://untrusted.example/archive"
    elif case == "tamper":
        artifacts.archive += b"changed"
    else:
        env["GITHUB_REF"] = "refs/heads/hackathon/nebius-nemotron-2026"
    with pytest.raises(shutdown.ShutdownError):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert not writes(fly)


def test_successful_cleanup_verifies_zero_and_repeated_execution_is_idempotent(prepared):
    fly, directory, certificate, artifacts, env = prepared
    result = shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert result["status"] == "retired"
    assert result["app_name_retained"] is True
    destructive = [(m, p) for m, p, _ in writes(fly) if not p.endswith("/exec")]
    assert destructive == [("POST", "/machines/" + shutdown.MACHINE + "/stop"),
        ("DELETE", "/machines/" + shutdown.MACHINE), ("DELETE", "/volumes/" + shutdown.VOLUME),
        ("DELETE", "/ip_assignments/66.241.124.22")]
    fly.calls.clear()
    assert shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE + timedelta(hours=1), env, artifacts)["status"] == "retired"
    assert not writes(fly)


def test_partial_failure_recovers_prior_run_backup_on_later_day(prepared, tmp_path):
    fly, directory, certificate, artifacts, env = prepared
    fly.fail_delete_volume = True
    with pytest.raises(shutdown.ShutdownError, match="Volume deletion"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert fly.machine is None and fly.volume is not None
    recovered = tmp_path / "recovered"
    result = shutdown.recover_backup(artifacts, recovered, certificate, shutdown.SHUTDOWN_DUE + timedelta(days=1), env)
    assert result["artifact_id"] == "321"
    fly.fail_delete_volume = False
    assert shutdown.execute(fly, recovered, certificate, shutdown.SHUTDOWN_DUE + timedelta(days=1), env, artifacts)["status"] == "retired"


def test_stopped_machine_retry_recovers_previous_day_backup_without_starting_it(prepared, tmp_path):
    fly, _, certificate, artifacts, env = prepared
    fly.machine["state"] = "stopped"
    recovered = tmp_path / "stopped-recovery"
    later = shutdown.SHUTDOWN_DUE + timedelta(days=1)
    shutdown.recover_backup(artifacts, recovered, certificate, later, env)
    fly.calls.clear()
    assert shutdown.execute(fly, recovered, certificate, later, env, artifacts)["status"] == "retired"
    assert not any(method == "POST" for method, _, _ in fly.calls)


def test_snapshot_disable_is_noop_when_deleted_volume_snapshot_endpoint_is_unknown(prepared):
    fly, *_ = prepared
    fly.machine = fly.volume = None
    original = fly.request
    def request(method, suffix="", body=None):
        if suffix.endswith("/snapshots"):
            error = shutdown.ShutdownError("The deleted volume has no list endpoint.")
            error.status = 404
            raise error
        return original(method, suffix, body)
    fly.request = request
    result = shutdown.disable_snapshots(fly, shutdown.SNAPSHOTS_DUE)
    assert result == {"status": "no_active_volume", "remaining_snapshots": None, "snapshot_inventory_available": False}
    assert not writes(fly)


@pytest.mark.parametrize("state,started", [("started", True), ("stopped", False), (None, False)])
def test_inventory_cli_reports_whether_backup_can_run_without_starting_machine(prepared, monkeypatch, capsys, state, started):
    fly, *_ = prepared
    if state is None:
        fly.machine = None
        fly.volume["attached_machine_id"] = None
    else:
        fly.machine["state"] = state
    monkeypatch.setattr(shutdown, "Fly", lambda token: fly)
    assert shutdown.main(["--mode", "inventory"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["machine_started"] is started
    assert not writes(fly)


def test_snapshot_api_error_is_not_reported_as_absence(prepared):
    fly, directory, certificate, artifacts, env = prepared
    fly.fail_snapshot_listing = True
    with pytest.raises(shutdown.ShutdownError, match="Snapshot list"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert not writes(fly)


def test_wait_is_bounded_and_does_not_delete_if_stop_never_finishes(prepared, monkeypatch):
    fly, directory, certificate, artifacts, env = prepared
    original = fly.request
    def request(method, suffix="", body=None):
        if method == "POST" and suffix.endswith("/stop"):
            fly.calls.append((method, suffix, body))
            return None
        return original(method, suffix, body)
    fly.request = request
    original_wait = shutdown.wait_for
    monkeypatch.setattr(shutdown, "wait_for", lambda f, predicate, message: original_wait(f, predicate, message, sleep=lambda seconds: None))
    with pytest.raises(shutdown.ShutdownError, match="bounded"):
        shutdown.execute(fly, directory, certificate, shutdown.SHUTDOWN_DUE, env, artifacts)
    assert not any(method == "DELETE" for method, _, _ in fly.calls)


def test_remote_aggregate_command_reads_consistent_snapshot_without_personal_data(tmp_path, monkeypatch, capsys):
    path = tmp_path / "operator.sqlite3"
    with sqlite3.connect(path) as db:
        db.executescript("CREATE TABLE calls(model,stage,state,input_tokens,output_tokens,actual,reserved,session_id); CREATE TABLE provider_health(stage,state);")
        db.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?,?)", ("nvidia/nemotron-3-super-120b-a12b", "generation", "completed", 100, 40, .000066, 0, "private-visitor-canary"))
    monkeypatch.setenv("EASY_STREET_DEMO_BUDGET_USD", "0")
    code = shutdown.AGGREGATE_COMMAND.replace("/var/lib/easy-street/operator-usage.sqlite3", path.as_posix())
    exec(compile(code, "<fixed-backup-command>", "exec"), {})
    output = capsys.readouterr().out
    assert "private-visitor-canary" not in output
    result = json.loads(output)
    assert result["paused"] is True and result["calls"][0][3:6] == [1, 100, 40]


def test_http_failure_messages_never_include_private_body_or_token(monkeypatch):
    import urllib.error
    http = shutdown.Http()
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError("https://private-token.example", 403, "private-token-and-error", {}, None)
    monkeypatch.setattr(http.opener, "open", fail)
    with pytest.raises(shutdown.ShutdownError) as caught:
        http.json("GET", "https://api.machines.dev/v1/apps/fixture", "private-token")
    assert "private-token" not in str(caught.value)
