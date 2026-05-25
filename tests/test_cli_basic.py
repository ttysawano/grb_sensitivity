import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "grb_sensitivity.cli", *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_help_exits_successfully():
    completed = run_cli("--help")

    assert completed.returncode == 0
    assert "grb-sens" in completed.stdout


def test_user_help_contains_quick_start():
    completed = run_cli("--user-help")

    assert completed.returncode == 0
    assert "Quick start" in completed.stdout
    assert "Response CSV format" in completed.stdout
    assert "Common warnings" in completed.stdout


def test_developer_help_contains_band_reference():
    completed = run_cli("--developer-help")

    assert completed.returncode == 0
    assert "Band (2003)" in completed.stdout
    assert "Moretti et al. (2009) CXB" in completed.stdout
    assert "Adding or modifying output columns" in completed.stdout


def test_help_subcommands_work():
    user = run_cli("help", "user")
    developer = run_cli("help", "developer")

    assert user.returncode == 0
    assert "Quick start" in user.stdout
    assert "Run curve mode" in user.stdout
    assert developer.returncode == 0
    assert "Package layout" in developer.stdout
    assert "Where equations live" in developer.stdout


def test_template_prints_yaml_like_template():
    completed = run_cli("template")

    assert completed.returncode == 0
    assert "version: 0.1" in completed.stdout
    assert "quantity: null" in completed.stdout


def test_validate_accepts_example_curve():
    completed = run_cli("validate", "--config", "examples/example_curve.yaml")

    assert completed.returncode == 0
    assert "Configuration is valid" in completed.stdout


def test_run_dry_run_prints_readable_summary():
    completed = run_cli("run", "--config", "examples/example_curve.yaml", "--dry-run")

    assert completed.returncode == 0
    assert "GRB sensitivity dry-run summary" in completed.stdout
    assert "mock Stage 1" in completed.stdout
