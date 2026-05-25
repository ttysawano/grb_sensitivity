"""Stage 3 command-line execution and output file helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import tempfile

import numpy as np
import pandas as pd

from .config_schema import ConfigError
from .detector import Detector
from .response import DetectorResponse
from .sensitivity import (
    background_counts_total,
    significance_sigma,
    source_counts,
    threshold_peak_photon_flux,
)
from .spectra import BandSpectrum


def run_from_config(config: dict[str, Any], config_path: str | Path) -> list[Path]:
    """Run the configured Stage 3 calculation and return written paths."""

    mode = config["mode"]
    if mode == "curve":
        return run_curve(config, config_path)
    if mode == "significance":
        return run_significance(config, config_path)
    raise ConfigError("mode must be either 'curve' or 'significance'.")


def run_curve(config: dict[str, Any], config_path: str | Path) -> list[Path]:
    """Generate a sensitivity curve CSV and optional PNG plot."""

    config_path = Path(config_path)
    detector = _detector_from_config(config, config_path)
    spectrum_cfg = config["spectrum"]
    trigger_cfg = config["detector"]["trigger"]
    background_cfg = config["background"]
    internal_cfg = background_cfg["internal"]
    cxb_cfg = background_cfg["cxb"]
    grid_cfg = config["curve"]["epeak_grid_keV"]
    n_grid = _integration_grid_num(config)

    E_1, E_2 = trigger_cfg["energy_band_keV"]
    E_l, E_h = config["flux"]["reference_band_keV"]
    Delta_t = float(trigger_cfg["accumulation_time_s"])
    sigma_0 = float(trigger_cfg["threshold_sigma"])
    R_int_cps = float(internal_cfg.get("rate_cps", 0.0))
    background = background_counts_total(
        detector,
        (E_1, E_2),
        Delta_t,
        R_int_cps=R_int_cps,
        cxb_enabled=bool(cxb_cfg.get("enabled", True)),
        cxb_model=cxb_cfg.get("model", "moretti2009"),
        below_valid_range_policy=cxb_cfg.get("below_valid_range_policy", "truncate_with_warning"),
        above_valid_range_policy=cxb_cfg.get("above_valid_range_policy", "evaluate_with_warning"),
        n_grid=n_grid,
    )

    rows: list[dict[str, float]] = []
    for E_p in _grid_values(grid_cfg):
        result = threshold_peak_photon_flux(
            alpha=float(spectrum_cfg["alpha"]),
            beta=float(spectrum_cfg["beta"]),
            epeak_keV=float(E_p),
            epivot_keV=float(spectrum_cfg["epivot_keV"]),
            detector=detector,
            trigger_band_keV=(E_1, E_2),
            reference_band_keV=(E_l, E_h),
            Delta_t=Delta_t,
            sigma_0=sigma_0,
            R_int_cps=R_int_cps,
            cxb_enabled=bool(cxb_cfg.get("enabled", True)),
            cxb_model=cxb_cfg.get("model", "moretti2009"),
            below_valid_range_policy=cxb_cfg.get("below_valid_range_policy", "truncate_with_warning"),
            above_valid_range_policy=cxb_cfg.get("above_valid_range_policy", "evaluate_with_warning"),
            precomputed_background=background,
            n_grid=n_grid,
        )
        rows.append(
            {
                "epeak_keV": result.epeak_keV,
                "threshold_photon_flux_ph_cm2_s": result.threshold_photon_flux_ph_cm2_s,
                "threshold_energy_flux_erg_cm2_s": result.threshold_energy_flux_erg_cm2_s,
                "source_counts_at_threshold": result.source_counts_at_threshold,
                "background_counts_total": result.background_counts_total,
                "background_counts_cxb": result.background_counts_cxb,
                "background_counts_internal": result.background_counts_internal,
                "trigger_energy_min_keV": float(E_1),
                "trigger_energy_max_keV": float(E_2),
                "sigma0": sigma_0,
            }
        )

    frame = pd.DataFrame(rows)
    csv_path = _resolve_output_path(config_path, config["output"]["csv"])
    _write_csv(frame, csv_path)
    written = [csv_path]

    plot_value = config["output"].get("plot")
    if plot_value:
        plot_path = _resolve_output_path(config_path, plot_value)
        _write_curve_plot(frame, plot_path)
        written.append(plot_path)
    return written


def run_significance(config: dict[str, Any], config_path: str | Path) -> list[Path]:
    """Generate a one-row significance CSV for a configured GRB."""

    config_path = Path(config_path)
    detector = _detector_from_config(config, config_path)
    spectrum_cfg = config["spectrum"]
    grb_cfg = config["grb"]
    peak_flux_cfg = grb_cfg["peak_flux"]
    trigger_cfg = config["detector"]["trigger"]
    background_cfg = config["background"]
    internal_cfg = background_cfg["internal"]
    cxb_cfg = background_cfg["cxb"]
    n_grid = _integration_grid_num(config)

    E_1, E_2 = trigger_cfg["energy_band_keV"]
    Delta_t = float(trigger_cfg["accumulation_time_s"])
    R_int_cps = float(internal_cfg.get("rate_cps", 0.0))
    peak_flux = float(peak_flux_cfg["value"])
    peak_flux_band = peak_flux_cfg["band_keV"]

    base_spectrum = BandSpectrum(
        alpha=float(spectrum_cfg["alpha"]),
        beta=float(spectrum_cfg["beta"]),
        epeak_keV=float(grb_cfg["epeak_keV"]),
        epivot_keV=float(spectrum_cfg["epivot_keV"]),
        N0=1.0,
    )
    normalized_spectrum = base_spectrum.renormalized_to_photon_flux(peak_flux, peak_flux_band, n_grid)
    S = source_counts(normalized_spectrum, detector, (E_1, E_2), Delta_t, n_grid=n_grid)
    background = background_counts_total(
        detector,
        (E_1, E_2),
        Delta_t,
        R_int_cps=R_int_cps,
        cxb_enabled=bool(cxb_cfg.get("enabled", True)),
        cxb_model=cxb_cfg.get("model", "moretti2009"),
        below_valid_range_policy=cxb_cfg.get("below_valid_range_policy", "truncate_with_warning"),
        above_valid_range_policy=cxb_cfg.get("above_valid_range_policy", "evaluate_with_warning"),
        n_grid=n_grid,
    )
    significance = significance_sigma(S, background.total)

    threshold_sigma = float(trigger_cfg["threshold_sigma"])
    row = {
        "grb_name": grb_cfg["name"],
        "alpha": float(spectrum_cfg["alpha"]),
        "beta": float(spectrum_cfg["beta"]),
        "epeak_keV": float(grb_cfg["epeak_keV"]),
        "peak_flux_ph_cm2_s": peak_flux,
        "peak_flux_band_min_keV": float(peak_flux_band[0]),
        "peak_flux_band_max_keV": float(peak_flux_band[1]),
        "source_counts": S,
        "background_counts_total": background.total,
        "background_counts_cxb": background.cxb,
        "background_counts_internal": background.internal,
        "significance_sigma": significance,
        "detected": significance >= threshold_sigma,
    }

    csv_path = _resolve_output_path(config_path, config["output"]["csv"])
    _write_csv(pd.DataFrame([row]), csv_path)
    return [csv_path]


def _detector_from_config(config: dict[str, Any], config_path: Path) -> Detector:
    detector_cfg = config["detector"]
    response_cfg = detector_cfg["response"]
    response_path = Path(response_cfg["path"])
    if not response_path.is_absolute():
        response_path = config_path.parent / response_path

    try:
        response = DetectorResponse.from_csv(
            response_path,
            quantity=response_cfg["quantity"],
            csv_has_header=bool(response_cfg.get("csv_has_header", True)),
            energy_column=response_cfg.get("energy_column", 1),
            value_column=response_cfg.get("value_column", 2),
            interpolation=response_cfg.get("interpolation", "loglog"),
            extrapolation=response_cfg.get("extrapolation", "powerlaw_with_warning"),
        )
        mask_cfg = detector_cfg["mask"]
        return Detector(
            response=response,
            geometric_area_cm2=float(detector_cfg["geometric_area_cm2"]),
            active_fraction=float(detector_cfg["active_fraction"]),
            aperture_solid_angle_sr=float(detector_cfg["aperture_solid_angle_sr"]),
            mask_open_fraction=float(mask_cfg["open_fraction"]),
            response_includes_mask=bool(mask_cfg.get("response_includes_mask", False)),
        )
    except (OSError, ValueError) as exc:
        raise ConfigError(str(exc)) from exc


def _grid_values(grid_cfg: dict[str, Any]) -> np.ndarray:
    E_min = float(grid_cfg["min"])
    E_max = float(grid_cfg["max"])
    n = int(grid_cfg["num"])
    if n < 2:
        raise ConfigError("curve.epeak_grid_keV.num must be at least 2.")
    if grid_cfg.get("spacing", "log") == "log":
        return np.logspace(np.log10(E_min), np.log10(E_max), n)
    if grid_cfg.get("spacing") == "linear":
        return np.linspace(E_min, E_max, n)
    raise ConfigError("curve.epeak_grid_keV.spacing must be 'log' or 'linear'.")


def _integration_grid_num(config: dict[str, Any]) -> int:
    return int(config.get("numerics", {}).get("integration_grid", {}).get("num", 4096))


def _resolve_output_path(config_path: Path, output_value: str | Path) -> Path:
    output_path = Path(output_value)
    if not output_path.is_absolute():
        output_path = config_path.parent / output_path
    return output_path


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _write_curve_plot(frame: pd.DataFrame, path: Path) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "grb_sensitivity_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot(frame["epeak_keV"], frame["threshold_photon_flux_ph_cm2_s"], color="tab:blue", linewidth=1.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Epeak [keV]")
    ax.set_ylabel("Threshold photon flux [ph cm^-2 s^-1]")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
