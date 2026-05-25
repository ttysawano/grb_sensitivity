"""Configuration defaults and validation for :mod:`grb_sensitivity`.

Stage 1 validates the scientific assumptions that are visible in YAML. The
actual Band (2003) sensitivity calculation is added in later stages, but these
checks already protect the units and conventions that the calculation will use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a YAML configuration is missing or scientifically invalid."""


@dataclass(frozen=True)
class ValidationResult:
    """Small structured return value used by the CLI."""

    config: dict[str, Any]
    warnings: list[str]


ALLOWED_MODES = {"curve", "significance"}
ALLOWED_RESPONSE_QUANTITIES = {"efficiency", "effective_area_cm2"}


def default_config(response_quantity: str | None = None) -> dict[str, Any]:
    """Return the v0.1 default configuration as a plain Python dictionary."""

    return {
        "version": 0.1,
        "mode": "curve",
        "spectrum": {
            "model": "band",
            "alpha": -1.0,
            "beta": -2.5,
            "epivot_keV": 100.0,
        },
        "flux": {
            "reference_band_keV": [1.0, 1000.0],
            "report_bands_keV": {
                "band2003_1_1000keV": [1.0, 1000.0],
                "lat_lle_30_100MeV": [30000.0, 100000.0],
            },
        },
        "curve": {
            "epeak_grid_keV": {
                "min": 10.0,
                "max": 10000.0,
                "num": 256,
                "spacing": "log",
            }
        },
        "grb": {
            "name": "example_grb",
            "epeak_keV": 500.0,
            "peak_flux": {
                "value": 1.0,
                "unit": "ph_cm2_s",
                "band_keV": [1.0, 1000.0],
            },
        },
        "detector": {
            "name": "grb_detector",
            "response": {
                "path": "detector_response.csv",
                "quantity": response_quantity,
                "csv_has_header": True,
                "energy_column": 1,
                "value_column": 2,
                "interpolation": "loglog",
                "extrapolation": "powerlaw_with_warning",
                "effective_area_includes_active_fraction": True,
                "effective_area_includes_mask": False,
            },
            "geometric_area_cm2": 100.0,
            "active_fraction": 1.0,
            "aperture_solid_angle_sr": 1.0,
            "mask": {
                "open_fraction": 1.0,
                "response_includes_mask": False,
                "apply_to_source": True,
                "apply_to_cxb": True,
            },
            "trigger": {
                "energy_band_keV": [10.0, 1000.0],
                "accumulation_time_s": 1.0,
                "threshold_sigma": 8.0,
                "statistic": "gaussian_s_over_sqrt_b",
            },
        },
        "background": {
            "cxb": {
                "enabled": True,
                "model": "moretti2009",
                "nominal_valid_energy_range_keV": [10.0, 200.0],
                "below_valid_range_policy": "truncate_with_warning",
                "above_valid_range_policy": "evaluate_with_warning",
            },
            "internal": {
                "mode": "trigger_band_rate",
                "rate_cps": 0.0,
            },
        },
        "numerics": {
            "integration_grid": {
                "num": 4096,
                "spacing": "log",
            }
        },
        "output": {
            "csv": "sensitivity_curve.csv",
            "plot": "sensitivity_curve.png",
        },
    }


def validate_config(config: dict[str, Any], *, config_path: Path | None = None) -> ValidationResult:
    """Validate required v0.1 YAML fields.

    The messages are deliberately plain English because students should be able
    to fix their input files without reading the source.
    """

    errors: list[str] = []
    warnings: list[str] = []

    def require_path(path: str) -> Any:
        value: Any = config
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                errors.append(f"{path} is required.")
                return None
            value = value[part]
        return value

    mode = require_path("mode")
    if mode is not None and mode not in ALLOWED_MODES:
        errors.append("mode must be either 'curve' or 'significance'.")

    require_path("version")
    spectrum_model = require_path("spectrum.model")
    if spectrum_model is not None and spectrum_model != "band":
        errors.append("spectrum.model must be 'band' in v0.1.")

    alpha = _as_float(require_path("spectrum.alpha"), "spectrum.alpha", errors)
    beta = _as_float(require_path("spectrum.beta"), "spectrum.beta", errors)
    if alpha is not None and alpha <= -2.0:
        errors.append("spectrum.alpha must be greater than -2 for Epeak to define E_0.")
    if alpha is not None and beta is not None and alpha <= beta:
        errors.append("spectrum.alpha must be greater than spectrum.beta.")

    response_path = require_path("detector.response.path")
    response_quantity = require_path("detector.response.quantity")
    require_path("detector.response.energy_column")
    require_path("detector.response.value_column")

    if response_quantity is None:
        errors.append("response.quantity is required. Choose either 'efficiency' or 'effective_area_cm2'.")
    elif response_quantity not in ALLOWED_RESPONSE_QUANTITIES:
        errors.append("response.quantity must be either 'efficiency' or 'effective_area_cm2'.")

    E_l, E_h = _band(require_path("flux.reference_band_keV"), "flux.reference_band_keV", errors)
    if E_l is not None and E_l <= 0:
        errors.append("flux.reference_band_keV lower energy must be positive.")
    if E_l is not None and E_h is not None and E_h <= E_l:
        errors.append("flux.reference_band_keV upper energy must be greater than the lower energy.")

    E_1, E_2 = _band(require_path("detector.trigger.energy_band_keV"), "detector.trigger.energy_band_keV", errors)
    if E_1 is not None and E_1 <= 0:
        errors.append("detector.trigger.energy_band_keV lower energy must be positive.")
    if E_1 is not None and E_2 is not None and E_2 <= E_1:
        errors.append("detector.trigger.energy_band_keV upper energy must be greater than the lower energy.")

    sigma_0 = _as_float(require_path("detector.trigger.threshold_sigma"), "detector.trigger.threshold_sigma", errors)
    if sigma_0 is not None and sigma_0 <= 0:
        errors.append("detector.trigger.threshold_sigma must be positive.")

    Delta_t = _as_float(require_path("detector.trigger.accumulation_time_s"), "detector.trigger.accumulation_time_s", errors)
    if Delta_t is not None and Delta_t <= 0:
        errors.append("detector.trigger.accumulation_time_s must be positive.")

    if response_quantity == "efficiency":
        A = _as_float(require_path("detector.geometric_area_cm2"), "detector.geometric_area_cm2", errors)
        if A is not None and A <= 0:
            errors.append("detector.geometric_area_cm2 must be positive when response.quantity is 'efficiency'.")

    f_det = _as_float(require_path("detector.active_fraction"), "detector.active_fraction", errors)
    if f_det is not None and not (0 < f_det <= 1):
        errors.append("detector.active_fraction must be greater than 0 and no larger than 1.")

    f_mask = _as_float(require_path("detector.mask.open_fraction"), "detector.mask.open_fraction", errors)
    if f_mask is not None and not (0 < f_mask <= 1):
        errors.append("detector.mask.open_fraction must be greater than 0 and no larger than 1.")

    cxb_enabled = bool(config.get("background", {}).get("cxb", {}).get("enabled", False))
    if cxb_enabled:
        Omega = _as_float(require_path("detector.aperture_solid_angle_sr"), "detector.aperture_solid_angle_sr", errors)
        if Omega is not None and Omega <= 0:
            errors.append("detector.aperture_solid_angle_sr must be positive when CXB background is enabled.")

    epeak = config.get("grb", {}).get("epeak_keV")
    if epeak is not None:
        epeak_value = _as_float(epeak, "grb.epeak_keV", errors)
        if epeak_value is not None and epeak_value <= 0:
            errors.append("grb.epeak_keV must be positive.")

    if response_path and config_path is not None:
        csv_path = Path(response_path)
        if not csv_path.is_absolute():
            csv_path = config_path.parent / csv_path
        if not csv_path.exists():
            warnings.append(f"response CSV was not found at {csv_path}; Stage 1 validation did not read response data.")

    if errors:
        raise ConfigError("\n".join(errors))
    return ValidationResult(config=config, warnings=warnings)


def _as_float(value: Any, field: str, errors: list[str]) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field} must be a number.")
        return None


def _band(value: Any, field: str, errors: list[str]) -> tuple[float | None, float | None]:
    if not isinstance(value, list) or len(value) != 2:
        errors.append(f"{field} must be a two-item list like [10.0, 1000.0].")
        return None, None
    return _as_float(value[0], f"{field}[0]", errors), _as_float(value[1], f"{field}[1]", errors)
