"""Interactive configuration creation for the CLI."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .config_io import DEFAULT_CONFIG_NAME
from .config_schema import ConfigError, default_config


def prompt_create_config(path: str | Path = DEFAULT_CONFIG_NAME) -> Path | None:
    """Create a configuration file interactively, returning the new path."""

    target = Path(path)
    if not sys.stdin.isatty():
        raise ConfigError(
            "No configuration file was found, and interactive mode is not available.\n"
            "Run `grb-sens init` in a terminal, or specify `--config path/to/config.yaml`."
        )

    config = build_config_interactively()
    print_config_summary(config, target)
    if not ask_yes_no(f"Write this configuration to {target}?", default=True):
        print("No configuration written.")
        return None

    if target.exists():
        backup = backup_existing_config(target)
        print(f"Existing configuration moved to: {backup}")
    target.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    print(f"Created configuration file: {target}")
    return target


def build_config_interactively() -> dict[str, Any]:
    """Ask the standard v0.1 questions and return a YAML-ready config dict."""

    mode = ask_choice("Calculation mode", choices=("curve", "significance"), default="curve")
    config = default_config(response_quantity=None)
    config["mode"] = mode

    detector = config["detector"]
    response = detector["response"]
    trigger = detector["trigger"]
    background = config["background"]
    spectrum = config["spectrum"]

    detector["name"] = ask_text("Detector name", detector["name"])
    response["path"] = ask_text("Response CSV path", response["path"])
    response["quantity"] = ask_response_quantity()
    response["csv_has_header"] = ask_yes_no("Whether the CSV has a header", default=True)
    response["energy_column"] = ask_column("Energy column name or 1-based column number", response["energy_column"])
    response["value_column"] = ask_column("Value column name or 1-based column number", response["value_column"])

    detector["geometric_area_cm2"] = ask_float("Geometric detector area [cm^2]", detector["geometric_area_cm2"], minimum=0.0)
    E_1 = ask_float("Trigger lower energy E_1 [keV]", trigger["energy_band_keV"][0], minimum=0.0)
    E_2 = ask_float("Trigger upper energy E_2 [keV]", trigger["energy_band_keV"][1], minimum=E_1)
    trigger["energy_band_keV"] = [E_1, E_2]
    trigger["accumulation_time_s"] = ask_float("Accumulation time Delta_t [s]", trigger["accumulation_time_s"], minimum=0.0)
    trigger["threshold_sigma"] = ask_float("Threshold significance sigma_0", trigger["threshold_sigma"], minimum=0.0)
    background["internal"]["rate_cps"] = ask_float(
        "Internal background rate in trigger band [counts/s]",
        background["internal"]["rate_cps"],
        minimum=0.0,
        allow_zero=True,
    )

    cxb_enabled = ask_yes_no("Use CXB background?", default=True)
    background["cxb"]["enabled"] = cxb_enabled
    if cxb_enabled:
        background["cxb"]["model"] = "moretti2009"
        detector["aperture_solid_angle_sr"] = ask_float(
            "Aperture solid angle Omega [sr]",
            detector["aperture_solid_angle_sr"],
            minimum=0.0,
        )

    spectrum["alpha"] = ask_float("Band alpha", spectrum["alpha"])
    spectrum["beta"] = ask_float("Band beta", spectrum["beta"])

    if mode == "curve":
        grid = config["curve"]["epeak_grid_keV"]
        grid["min"] = ask_float("Epeak grid minimum [keV]", grid["min"], minimum=0.0)
        grid["max"] = ask_float("Epeak grid maximum [keV]", grid["max"], minimum=grid["min"])
        grid["num"] = ask_int("Epeak grid number of points", grid["num"], minimum=2)
        config["output"]["csv"] = ask_text("Output CSV path", "sensitivity_curve.csv")
        config["output"]["plot"] = ask_text("Output plot path for curve mode", "sensitivity_curve.png")
    else:
        grb = config["grb"]
        peak_flux = grb["peak_flux"]
        grb["name"] = ask_text("GRB name", grb["name"])
        grb["epeak_keV"] = ask_float("GRB Epeak [keV]", grb["epeak_keV"], minimum=0.0)
        peak_flux["value"] = ask_float("Peak photon flux value [ph cm^-2 s^-1]", peak_flux["value"], minimum=0.0)
        band_low = ask_float("Peak flux band lower energy [keV]", peak_flux["band_keV"][0], minimum=0.0)
        band_high = ask_float("Peak flux band upper energy [keV]", peak_flux["band_keV"][1], minimum=band_low)
        peak_flux["band_keV"] = [band_low, band_high]
        config["output"]["csv"] = ask_text("Output CSV path", "significance_result.csv")
        config["output"]["plot"] = None

    return config


def ask_response_quantity() -> str:
    """Prompt until the required response.quantity has been chosen."""

    while True:
        print("Select detector response quantity:")
        print("  1) efficiency          - CSV value is dimensionless detection efficiency")
        print("  2) effective_area_cm2  - CSV value already includes collecting area")
        choice = input("Enter choice [1/2]: ").strip()
        if choice == "1":
            return "efficiency"
        if choice == "2":
            return "effective_area_cm2"
        print("Please enter 1 or 2.")


def ask_text(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return default if value == "" else value


def ask_choice(prompt: str, *, choices: tuple[str, ...], default: str) -> str:
    choices_text = "/".join(choices)
    while True:
        value = input(f"{prompt} [{default}]: ").strip().lower()
        if value == "":
            return default
        if value in choices:
            return value
        print(f"Please enter one of: {choices_text}.")


def ask_yes_no(prompt: str, *, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        value = input(f"{prompt} {suffix} ").strip().lower()
        if value == "":
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def ask_float(prompt: str, default: float, *, minimum: float | None = None, allow_zero: bool = False) -> float:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        text = str(default) if value == "" else value
        try:
            number = float(text)
        except ValueError:
            print("Please enter a number.")
            continue
        if minimum is not None:
            if allow_zero:
                valid = number >= minimum
                relation = f">= {minimum}"
            else:
                valid = number > minimum
                relation = f"> {minimum}"
            if not valid:
                print(f"Please enter a value {relation}.")
                continue
        return number


def ask_int(prompt: str, default: int, *, minimum: int | None = None) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        text = str(default) if value == "" else value
        try:
            number = int(text)
        except ValueError:
            print("Please enter an integer.")
            continue
        if minimum is not None and number < minimum:
            print(f"Please enter an integer >= {minimum}.")
            continue
        return number


def ask_column(prompt: str, default: int | str) -> int | str:
    value = input(f"{prompt} [{default}]: ").strip()
    if value == "":
        return default
    if value.isdigit():
        return int(value)
    return value


def print_config_summary(config: dict[str, Any], target: Path) -> None:
    detector = config["detector"]
    response = detector["response"]
    trigger = detector["trigger"]
    spectrum = config["spectrum"]
    output = config["output"]
    print("\nConfiguration summary")
    print(f"  file: {target}")
    print(f"  mode: {config['mode']}")
    print(f"  detector: {detector['name']}")
    print(f"  response: {response['path']} ({response['quantity']})")
    print(f"  trigger band: {trigger['energy_band_keV'][0]}-{trigger['energy_band_keV'][1]} keV")
    print(f"  accumulation time: {trigger['accumulation_time_s']} s")
    print(f"  threshold sigma: {trigger['threshold_sigma']}")
    print(f"  internal background: {config['background']['internal']['rate_cps']} counts/s")
    print(f"  CXB enabled: {config['background']['cxb']['enabled']}")
    print(f"  Band alpha/beta: {spectrum['alpha']} / {spectrum['beta']}")
    print(f"  output CSV: {output['csv']}")
    if output.get("plot"):
        print(f"  output plot: {output['plot']}")


def backup_existing_config(path: Path) -> Path:
    """Rename an existing config with the required timestamped backup name."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}_{timestamp}{path.suffix}.bak")
    path.rename(backup)
    return backup


def run_default_interactive_flow() -> int:
    """Behavior for running ``grb-sens`` without a subcommand."""

    config_path = Path(DEFAULT_CONFIG_NAME)
    if not sys.stdin.isatty():
        if config_path.exists():
            print(f"Found configuration file: {config_path}")
            print("Non-interactive mode cannot confirm running it. Use `grb-sens run --config grb_sensitivity.yaml --dry-run`.")
            return 2
        print(
            "No configuration file was found, and interactive mode is not available.\n"
            "Run `grb-sens init` in a terminal, or specify `--config path/to/config.yaml`.",
            file=sys.stderr,
        )
        return 2

    if not config_path.exists():
        print("No configuration file was found in the current directory.")
        answer = input("Would you like to create a new grb_sensitivity.yaml interactively? [Y/n] ").strip().lower()
        if answer in {"", "y", "yes"}:
            prompt_create_config(config_path)
            return 0
        print("No configuration created.")
        return 1

    print(f"Found configuration file: {config_path}")
    answer = input("Use this configuration and run the calculation? [Y/n] ").strip().lower()
    if answer in {"", "y", "yes"}:
        print("Stage 1 mock run: use `grb-sens run --config grb_sensitivity.yaml --dry-run` for the summary.")
        return 0

    answer = input("Would you like to create a new grb_sensitivity.yaml interactively? [Y/n] ").strip().lower()
    if answer in {"", "y", "yes"}:
        prompt_create_config(config_path)
        return 0
    print("No calculation run and no configuration created.")
    return 1
