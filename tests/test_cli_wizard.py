import builtins
import sys
from pathlib import Path

from grb_sensitivity.config_io import load_and_validate
from grb_sensitivity.wizard import ask_response_quantity, prompt_create_config, run_default_interactive_flow


class TtyStdin:
    def isatty(self):
        return True


def feed_inputs(monkeypatch, answers):
    prompts = []
    iterator = iter(answers)
    def fake_input(prompt=""):
        prompts.append(prompt)
        return next(iterator)

    monkeypatch.setattr(builtins, "input", fake_input)
    return prompts


def default_curve_answers(response_quantity="1", write=""):
    return [
        "",  # Calculation mode [curve]
        "",  # Detector name
        "",  # Response CSV path
        response_quantity,
        "",  # CSV has header
        "",  # Energy column
        "",  # Value column
        "",  # Geometric area
        "",  # E_1
        "",  # E_2
        "",  # Delta_t
        "",  # sigma_0
        "",  # internal background
        "",  # use CXB
        "",  # aperture solid angle
        "",  # Band alpha
        "",  # Band beta
        "",  # Epeak grid min
        "",  # Epeak grid max
        "",  # Epeak grid num
        "",  # output CSV
        "",  # output plot
        write,
    ]


def test_no_config_found_prompts_to_create_config(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    prompts = feed_inputs(monkeypatch, ["y", *default_curve_answers()])

    status = run_default_interactive_flow()

    assert status == 0
    assert (tmp_path / "grb_sensitivity.yaml").exists()
    assert "No configuration file was found" in capsys.readouterr().out
    prompt_text = "\n".join(prompts)
    assert "Detector name [grb_detector]" in prompt_text
    assert "Response CSV path [detector_response.csv]" in prompt_text
    assert "Trigger lower energy E_1 [keV] [10.0]" in prompt_text
    assert "Trigger upper energy E_2 [keV] [1000.0]" in prompt_text
    assert "Accumulation time Delta_t [s] [1.0]" in prompt_text
    assert "Threshold significance sigma_0 [8.0]" in prompt_text
    assert "Internal background rate in trigger band [counts/s] [0.0]" in prompt_text
    assert "Aperture solid angle Omega [sr] [1.0]" in prompt_text
    assert "Band alpha [-1.0]" in prompt_text
    assert "Band beta [-2.5]" in prompt_text
    assert "Epeak grid minimum [keV] [10.0]" in prompt_text
    assert "Epeak grid maximum [keV] [10000.0]" in prompt_text
    assert "Epeak grid number of points [256]" in prompt_text


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
    feed_inputs(monkeypatch, ["n", "y", *default_curve_answers(response_quantity="2")])

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
    feed_inputs(monkeypatch, default_curve_answers())

    path = prompt_create_config("grb_sensitivity.yaml")
    Path("detector_response.csv").write_text("energy_keV,efficiency\n1,0.5\n10,0.6\n", encoding="utf-8")
    result = load_and_validate(path)

    assert result.config["detector"]["response"]["quantity"] == "efficiency"


def test_declining_final_write_does_not_create_config(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "stdin", TtyStdin())
    feed_inputs(monkeypatch, default_curve_answers(write="n"))

    path = prompt_create_config("grb_sensitivity.yaml")

    assert path is None
    assert not Path("grb_sensitivity.yaml").exists()
    assert "No configuration written." in capsys.readouterr().out
