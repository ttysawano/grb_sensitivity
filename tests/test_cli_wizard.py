import builtins
import sys
from pathlib import Path

from grb_sensitivity.config_io import load_and_validate
from grb_sensitivity.wizard import ask_response_quantity, prompt_create_config, run_default_interactive_flow


class TtyStdin:
    def isatty(self):
        return True


def feed_inputs(monkeypatch, answers):
    iterator = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(iterator))


def test_no_config_found_prompts_to_create_config(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    feed_inputs(monkeypatch, ["y", "1"])

    status = run_default_interactive_flow()

    assert status == 0
    assert (tmp_path / "grb_sensitivity.yaml").exists()
    assert "No configuration file was found" in capsys.readouterr().out


def test_existing_config_found_prompts_to_use_it(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    Path("grb_sensitivity.yaml").write_text("version: 0.1\n", encoding="utf-8")
    feed_inputs(monkeypatch, ["y"])

    status = run_default_interactive_flow()

    assert status == 0
    out = capsys.readouterr().out
    assert "Found configuration file: grb_sensitivity.yaml" in out
    assert "Stage 1 mock run" in out


def test_existing_config_declined_and_new_config_created_with_backup(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    Path("grb_sensitivity.yaml").write_text("old: true\n", encoding="utf-8")
    feed_inputs(monkeypatch, ["n", "y", "2"])

    status = run_default_interactive_flow()

    assert status == 0
    backups = list(tmp_path.glob("grb_sensitivity_*.yaml.bak"))
    assert len(backups) == 1
    assert "old: true" in backups[0].read_text(encoding="utf-8")
    assert "quantity: effective_area_cm2" in Path("grb_sensitivity.yaml").read_text(encoding="utf-8")


def test_response_quantity_cannot_be_empty(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["", "1"])

    assert ask_response_quantity() == "efficiency"
    assert "Please enter 1 or 2." in capsys.readouterr().out


def test_invalid_response_quantity_selection_reprompts(monkeypatch, capsys):
    feed_inputs(monkeypatch, ["3", "2"])

    assert ask_response_quantity() == "effective_area_cm2"
    assert "Please enter 1 or 2." in capsys.readouterr().out


def test_generated_yaml_validates(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    feed_inputs(monkeypatch, ["1"])

    path = prompt_create_config("grb_sensitivity.yaml")
    result = load_and_validate(path)

    assert result.config["detector"]["response"]["quantity"] == "efficiency"
