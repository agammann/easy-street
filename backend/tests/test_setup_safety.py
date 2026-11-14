"""Masked setup tests use temporary fixture keys only; no provider calls."""
from getpass import GetPassWarning
import os
from types import SimpleNamespace
import warnings

from dotenv import dotenv_values
import pytest

from scripts import configure_nebius
from scripts.live_nebius_check import exclusive_acceptance_lock


FIXTURE_KEY = "private-nebius-fixture-key-only"
EXISTING = "# Private local test settings\nOPENAI_API_KEY=openai-fixture-key-only\nEASY_STREET_BUDGET_USD=3.50\nEASY_STREET_DATA_DIR=original-data\n"


def test_nebius_key_save_preserves_openai_budget_and_other_local_settings(tmp_path,capsys):
    target=tmp_path/".env.local"
    target.write_text(EXISTING+"NEBIUS_API_KEY=previous-fixture-key\nexport NEBIUS_API_KEY=duplicate-fixture-key\n",encoding="utf-8")
    configure_nebius.save_key(FIXTURE_KEY,target)
    values=dotenv_values(target,interpolate=False)
    assert values == {"OPENAI_API_KEY":"openai-fixture-key-only","EASY_STREET_BUDGET_USD":"3.50",
        "EASY_STREET_DATA_DIR":"original-data","NEBIUS_API_KEY":FIXTURE_KEY}
    assert target.read_text(encoding="utf-8").count("NEBIUS_API_KEY=") == 1
    assert "# Private local test settings" in target.read_text(encoding="utf-8")
    assert not list(tmp_path.glob(".env-setup-*"))
    assert FIXTURE_KEY not in capsys.readouterr().out
    if os.name != "nt":
        assert target.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("invalid",[
    "too-short", "x"*5001, "a key with spaces", "fixture-key\nsecond-line",
    "fixture-key\"quoted", "fixture-key'quoted", "fixture-key\\slash",
    "fixture-key#comment", "fixture-key${OPENAI_API_KEY}", "fixture-key\x00null",
    "fixture-key\x7fdelete", "fixture-key-caf\u00e9",
])
def test_invalid_or_interpolated_key_cannot_change_existing_openai_settings(tmp_path,invalid):
    target=tmp_path/".env.local"
    target.write_text(EXISTING,encoding="utf-8")
    with pytest.raises(ValueError,match="Invalid key"):
        configure_nebius.save_key(invalid,target)
    assert target.read_text(encoding="utf-8") == EXISTING
    assert not list(tmp_path.glob(".env-setup-*"))


def test_noninteractive_setup_stops_before_reading_or_saving_a_key(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(configure_nebius,"ROOT",tmp_path)
    monkeypatch.setattr(configure_nebius.sys,"stdin",SimpleNamespace(isatty=lambda:False))
    monkeypatch.setattr(configure_nebius,"getpass",lambda _:pytest.fail("Redirected input must not reach a credential prompt."))
    with pytest.raises(SystemExit,match="interactive"):
        configure_nebius.main()
    assert not (tmp_path/".env.local").exists()
    assert FIXTURE_KEY not in capsys.readouterr().out


def test_interactive_setup_uses_masked_prompt_and_never_echoes_key(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(configure_nebius,"ROOT",tmp_path)
    target=tmp_path/".env.local"
    target.write_text(EXISTING,encoding="utf-8")
    monkeypatch.setattr(configure_nebius.sys,"stdin",SimpleNamespace(isatty=lambda:True))
    prompts=[]
    def masked(prompt):
        prompts.append(prompt)
        return FIXTURE_KEY
    monkeypatch.setattr(configure_nebius,"getpass",masked)
    monkeypatch.setattr("builtins.input",lambda _:pytest.fail("Plain credential input is forbidden."))
    configure_nebius.main()
    assert len(prompts) == 1 and "hidden" in prompts[0].lower()
    assert dotenv_values(target,interpolate=False)["NEBIUS_API_KEY"] == FIXTURE_KEY
    output=capsys.readouterr()
    assert FIXTURE_KEY not in output.out+output.err
    assert "openai-fixture-key-only" not in output.out+output.err


def test_echo_fallback_warning_aborts_without_saving_any_key(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(configure_nebius,"ROOT",tmp_path)
    target=tmp_path/".env.local"
    target.write_text(EXISTING,encoding="utf-8")
    monkeypatch.setattr(configure_nebius.sys,"stdin",SimpleNamespace(isatty=lambda:True))
    def unavailable_echo_control(_):
        warnings.warn("Cannot disable terminal echo.",GetPassWarning)
        pytest.fail("A getpass fallback must abort before it can echo input.")
    monkeypatch.setattr(configure_nebius,"getpass",unavailable_echo_control)
    with pytest.raises(SystemExit,match="(?i)(echo|masked|private terminal)"):
        configure_nebius.main()
    assert target.read_text(encoding="utf-8") == EXISTING
    assert FIXTURE_KEY not in capsys.readouterr().out


def test_cancelled_setup_preserves_existing_file(tmp_path,monkeypatch):
    monkeypatch.setattr(configure_nebius,"ROOT",tmp_path)
    target=tmp_path/".env.local"
    target.write_text(EXISTING,encoding="utf-8")
    monkeypatch.setattr(configure_nebius.sys,"stdin",SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr(configure_nebius,"getpass",lambda _:"")
    configure_nebius.main()
    assert target.read_text(encoding="utf-8") == EXISTING


def test_atomic_save_failure_keeps_existing_credentials_and_removes_temporary_file(tmp_path,monkeypatch):
    target=tmp_path/".env.local"
    target.write_text(EXISTING,encoding="utf-8")
    def unavailable_replace(*_):
        raise OSError("Simulated atomic replacement failure.")
    monkeypatch.setattr(configure_nebius.os,"replace",unavailable_replace)
    with pytest.raises(OSError,match="replacement failure"):
        configure_nebius.save_key(FIXTURE_KEY,target)
    assert target.read_text(encoding="utf-8") == EXISTING
    assert not list(tmp_path.glob(".env-setup-*"))


def test_setup_refuses_to_replace_a_configuration_symlink(tmp_path):
    real=tmp_path/"original.env"
    real.write_text(EXISTING,encoding="utf-8")
    link=tmp_path/".env.local"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("This host cannot create a test symbolic link.")
    with pytest.raises(ValueError,match="symbolic link"):
        configure_nebius.save_key(FIXTURE_KEY,link)
    assert real.read_text(encoding="utf-8") == EXISTING


def test_live_acceptance_lock_excludes_a_second_run_and_releases_on_success(tmp_path):
    with exclusive_acceptance_lock(tmp_path) as path:
        assert path.name == "active.lock" and path.exists()
        with pytest.raises(SystemExit,match="previous run left its safety lock"):
            with exclusive_acceptance_lock(tmp_path):
                pytest.fail("A second process must not reach catalog or inference work.")
        assert FIXTURE_KEY not in path.read_text(encoding="utf-8")
    assert not path.exists()
    with exclusive_acceptance_lock(tmp_path):
        pass
    assert not path.exists()


@pytest.mark.parametrize("interruption",[RuntimeError("incomplete acceptance fixture"),KeyboardInterrupt()])
def test_interrupted_live_acceptance_retains_lock_for_manual_ledger_review(tmp_path,interruption):
    with pytest.raises(type(interruption)):
        with exclusive_acceptance_lock(tmp_path):
            raise interruption
    path=tmp_path/"active.lock"
    assert path.exists()
    with pytest.raises(SystemExit,match="review its durable ledger"):
        with exclusive_acceptance_lock(tmp_path):
            pytest.fail("Failed requests must never be automatically replayed.")
    assert path.exists()
