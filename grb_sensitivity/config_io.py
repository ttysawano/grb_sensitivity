"""YAML input and template output helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .config_schema import ConfigError, default_config, validate_config


DEFAULT_CONFIG_NAME = "grb_sensitivity.yaml"


TEMPLATE_YAML = """# GRB Sensitivity Calculator configuration, v0.1
# This Stage 1 template is valid YAML. Comments explain the scientific meaning
# of the fields that later stages use for the Band (2003) calculation.
version: 0.1

# Calculation mode: curve or significance. Stage 1 run is a dry-run summary.
mode: curve

spectrum:
  model: band
  alpha: -1.0
  beta: -2.5
  epivot_keV: 100.0

flux:
  reference_band_keV: [1.0, 1000.0]
  report_bands_keV:
    band2003_1_1000keV: [1.0, 1000.0]
    lat_lle_30_100MeV: [30000.0, 100000.0]

curve:
  epeak_grid_keV:
    min: 10.0
    max: 10000.0
    num: 256
    spacing: log

grb:
  name: example_grb
  epeak_keV: 500.0
  peak_flux:
    value: 1.0
    unit: ph_cm2_s
    band_keV: [1.0, 1000.0]

detector:
  name: grb_detector

  response:
    path: detector_response.csv
    # Required: choose efficiency or effective_area_cm2 before validation.
    quantity: null
    csv_has_header: true
    energy_column: 1
    value_column: 2
    interpolation: loglog
    extrapolation: powerlaw_with_warning
    effective_area_includes_active_fraction: true
    effective_area_includes_mask: false

  geometric_area_cm2: 100.0
  active_fraction: 1.0
  aperture_solid_angle_sr: 1.0

  mask:
    open_fraction: 1.0
    response_includes_mask: false
    apply_to_source: true
    apply_to_cxb: true

  trigger:
    energy_band_keV: [10.0, 1000.0]
    accumulation_time_s: 1.0
    threshold_sigma: 8.0
    statistic: gaussian_s_over_sqrt_b

background:
  cxb:
    enabled: true
    model: moretti2009
    nominal_valid_energy_range_keV: [10.0, 200.0]
    below_valid_range_policy: truncate_with_warning
    above_valid_range_policy: evaluate_with_warning

  internal:
    # In Band (2003), B_int is written as a differential internal background
    # term. In this v0.1 implementation, the main user-facing internal
    # background input is R_int_cps, already integrated over [E_1, E_2].
    mode: trigger_band_rate
    rate_cps: 0.0

numerics:
  integration_grid:
    num: 4096
    spacing: log

output:
  csv: sensitivity_curve.csv
  plot: sensitivity_curve.png
"""


def load_config(path: str | Path) -> dict[str, Any]:
    """Load YAML from *path* and return a mapping."""

    config_path = Path(path)
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file was not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Configuration YAML could not be parsed: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Configuration YAML must contain a top-level mapping.")
    return data


def load_and_validate(path: str | Path):
    """Load and validate a YAML configuration file."""

    config_path = Path(path)
    return validate_config(load_config(config_path), config_path=config_path)


def template_text(*, response_quantity: str | None = None) -> str:
    """Return a commented YAML template.

    If *response_quantity* is supplied, only the required quantity line is
    changed; this is used by the interactive wizard after the student chooses.
    """

    if response_quantity is None:
        return TEMPLATE_YAML
    return TEMPLATE_YAML.replace("quantity: null", f"quantity: {response_quantity}")


def write_template(path: str | Path, *, response_quantity: str | None = None) -> Path:
    target = Path(path)
    if target.exists():
        raise ConfigError(f"Refusing to overwrite existing configuration file: {target}")
    target.write_text(template_text(response_quantity=response_quantity), encoding="utf-8")
    return target


def example_config(response_quantity: str) -> dict[str, Any]:
    """Return defaults adjusted for bundled examples."""

    config = default_config(response_quantity=response_quantity)
    if response_quantity == "efficiency":
        config["detector"]["response"]["path"] = "detector_response_efficiency.csv"
    else:
        config["detector"]["response"]["path"] = "detector_response_effective_area.csv"
    return config
