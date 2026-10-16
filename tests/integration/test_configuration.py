from pathlib import Path
import pytest
import configure


def test_configuration_preserves_other_settings_and_keeps_key_hidden(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(configure,"ROOT",tmp_path)
    target = tmp_path / ".env.local"
    target.write_text("EASY_STREET_DATA_DIR=somewhere\nOPENAI_API_KEY=sk-old\nEASY_STREET_BUDGET_USD=1\n")
    monkeypatch.setattr(configure,"getpass",lambda _: "sk-test")
    monkeypatch.setattr("builtins.input",lambda _: "3.50")
    configure.main()
    assert "sk-test" not in capsys.readouterr().out
    assert target.read_text() == "EASY_STREET_DATA_DIR=somewhere\nOPENAI_API_KEY=sk-test\nEASY_STREET_BUDGET_USD=3.50\n"


@pytest.mark.parametrize("budget",["nan","Infinity","-1","not-money","10001"])
def test_invalid_configuration_preserves_existing_file(tmp_path, monkeypatch, budget):
    monkeypatch.setattr(configure,"ROOT",tmp_path)
    target = tmp_path / ".env.local"
    target.write_text("OPENAI_API_KEY=sk-old\n")
    monkeypatch.setattr(configure,"getpass",lambda _: "sk-test")
    monkeypatch.setattr("builtins.input",lambda _: budget)
    with pytest.raises(SystemExit):
        configure.main()
    assert target.read_text() == "OPENAI_API_KEY=sk-old\n"
