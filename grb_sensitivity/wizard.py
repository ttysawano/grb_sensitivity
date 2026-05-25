"""Interactive configuration creation for the Stage 1 CLI."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from .config_io import DEFAULT_CONFIG_NAME, write_template
from .config_schema import ConfigError


def prompt_create_config(path: str | Path = DEFAULT_CONFIG_NAME) -> Path | None:
    """Create a configuration file interactively, returning the new path."""

    target = Path(path)
    if not sys.stdin.isatty():
        raise ConfigError(
            "No configuration file was found, and interactive mode is not available.\n"
            "Run `grb-sens init` in a terminal, or specify `--config path/to/config.yaml`."
        )

    quantity = ask_response_quantity()
    if target.exists():
        backup = backup_existing_config(target)
        print(f"Existing configuration moved to: {backup}")
    write_template(target, response_quantity=quantity)
    print(f"Created configuration file: {target}")
    return target


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
