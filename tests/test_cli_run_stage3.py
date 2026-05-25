import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "grb_sensitivity.cli", *args],
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )


def copy_example_inputs(tmp_path: Path) -> Path:
    examples = tmp_path / "examples"
    examples.mkdir()
    for name in [
        "example_curve.yaml",
        "example_significance.yaml",
        "detector_response_efficiency.csv",
        "detector_response_effective_area.csv",
    ]:
        shutil.copy(Path("examples") / name, examples / name)
    curve_config = yaml.safe_load((examples / "example_curve.yaml").read_text(encoding="utf-8"))
    curve_config["curve"]["epeak_grid_keV"]["num"] = 8
    (examples / "example_curve.yaml").write_text(yaml.safe_dump(curve_config, sort_keys=False), encoding="utf-8")
    return examples


def test_cli_run_curve_writes_csv_and_png(tmp_path):
    examples = copy_example_inputs(tmp_path)
    completed = run_cli("run", "--config", str(examples / "example_curve.yaml"))

    assert completed.returncode == 0, completed.stderr
    csv_path = examples / "output" / "example_curve.csv"
    png_path = examples / "output" / "example_curve.png"
    assert csv_path.exists()
    assert png_path.exists()

    frame = pd.read_csv(csv_path)
    required = {
        "epeak_keV",
        "threshold_photon_flux_ph_cm2_s",
        "threshold_energy_flux_erg_cm2_s",
        "source_counts_at_threshold",
        "background_counts_total",
        "background_counts_cxb",
        "background_counts_internal",
        "trigger_energy_min_keV",
        "trigger_energy_max_keV",
        "sigma0",
    }
    assert required.issubset(frame.columns)
    assert len(frame) == 8


def test_cli_run_significance_writes_csv(tmp_path):
    examples = copy_example_inputs(tmp_path)
    completed = run_cli("run", "--config", str(examples / "example_significance.yaml"))

    assert completed.returncode == 0, completed.stderr
    csv_path = examples / "output" / "example_significance.csv"
    assert csv_path.exists()

    frame = pd.read_csv(csv_path)
    required = {
        "grb_name",
        "alpha",
        "beta",
        "epeak_keV",
        "peak_flux_ph_cm2_s",
        "peak_flux_band_min_keV",
        "peak_flux_band_max_keV",
        "source_counts",
        "background_counts_total",
        "background_counts_cxb",
        "background_counts_internal",
        "significance_sigma",
        "detected",
    }
    assert required.issubset(frame.columns)
    assert len(frame) == 1


def test_cli_dry_run_stays_summary_only(tmp_path):
    examples = copy_example_inputs(tmp_path)
    completed = run_cli("run", "--config", str(examples / "example_curve.yaml"), "--dry-run")

    assert completed.returncode == 0
    assert "GRB sensitivity dry-run summary" in completed.stdout
    assert not (examples / "output" / "example_curve.csv").exists()
