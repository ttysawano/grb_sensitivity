"""Command-line interface for ``grb-sens``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config_io import DEFAULT_CONFIG_NAME, load_and_validate, template_text, write_template
from .config_schema import ConfigError
from .help_text import DEVELOPER_HELP, USER_HELP
from .wizard import run_default_interactive_flow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grb-sens",
        description="Educational Band (2003)-style GRB detector sensitivity calculator.",
    )
    parser.add_argument("--user-help", action="store_true", help="print the user manual and exit")
    parser.add_argument("--developer-help", action="store_true", help="print the developer guide and exit")

    subparsers = parser.add_subparsers(dest="command")

    help_parser = subparsers.add_parser("help", help="print extended help")
    help_parser.add_argument("topic", choices=["user", "developer"])

    init_parser = subparsers.add_parser("init", help="create grb_sensitivity.yaml interactively")
    init_parser.add_argument("--config", default=DEFAULT_CONFIG_NAME, help="configuration path to create")

    template_parser = subparsers.add_parser("template", help="print a commented YAML template")
    template_parser.add_argument("--output", help="write the template to this path instead of stdout")

    validate_parser = subparsers.add_parser("validate", help="validate a YAML configuration")
    validate_parser.add_argument("--config", required=True, help="path to YAML configuration")

    run_parser = subparsers.add_parser("run", help="run or summarize a YAML configuration")
    run_parser.add_argument("--config", required=True, help="path to YAML configuration")
    run_parser.add_argument("--dry-run", action="store_true", help="validate and summarize without calculating")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.user_help:
        print(USER_HELP)
        return 0
    if args.developer_help:
        print(DEVELOPER_HELP)
        return 0
    if args.command is None:
        return run_default_interactive_flow()

    try:
        if args.command == "help":
            print(USER_HELP if args.topic == "user" else DEVELOPER_HELP)
            return 0
        if args.command == "init":
            return _cmd_init(Path(args.config))
        if args.command == "template":
            return _cmd_template(args.output)
        if args.command == "validate":
            return _cmd_validate(Path(args.config))
        if args.command == "run":
            return _cmd_run(Path(args.config), dry_run=args.dry_run)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser.error("unknown command")
    return 2


def _cmd_init(path: Path) -> int:
    from .wizard import prompt_create_config

    prompt_create_config(path)
    return 0


def _cmd_template(output: str | None) -> int:
    text = template_text()
    if output:
        write_template(output)
        print(f"Wrote template: {output}")
    else:
        print(text, end="")
    return 0


def _cmd_validate(config_path: Path) -> int:
    result = load_and_validate(config_path)
    for warning in result.warnings:
        print(f"Warning: {warning}")
    print(f"Configuration is valid: {config_path}")
    return 0


def _cmd_run(config_path: Path, *, dry_run: bool) -> int:
    result = load_and_validate(config_path)
    config = result.config
    for warning in result.warnings:
        print(f"Warning: {warning}")
    if not dry_run:
        print("Stage 1 mock run only. Re-run with --dry-run to see the configuration summary.")
        return 0
    print(_dry_run_summary(config_path, config))
    return 0


def _dry_run_summary(config_path: Path, config: dict) -> str:
    detector = config["detector"]
    response = detector["response"]
    trigger = detector["trigger"]
    spectrum = config["spectrum"]
    lines = [
        "GRB sensitivity dry-run summary",
        f"  config: {config_path}",
        f"  mode: {config['mode']}",
        f"  spectrum: {spectrum['model']} alpha={spectrum['alpha']} beta={spectrum['beta']} Epivot={spectrum['epivot_keV']} keV",
        f"  response: {response['path']} ({response['quantity']})",
        f"  detector: {detector['name']} area={detector['geometric_area_cm2']} cm^2 active_fraction={detector['active_fraction']}",
        f"  trigger band: {trigger['energy_band_keV'][0]}-{trigger['energy_band_keV'][1]} keV",
        f"  accumulation time Delta_t: {trigger['accumulation_time_s']} s",
        f"  threshold sigma_0: {trigger['threshold_sigma']}",
        "  calculation: mock Stage 1 validation summary; real physics is not run yet",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
