# Stage 1 CLI Review Notes

## Implemented commands

- `python -m grb_sensitivity.cli --help`
- `grb-sens --help`
- `grb-sens --user-help`
- `grb-sens --developer-help`
- `grb-sens help user`
- `grb-sens help developer`
- `grb-sens init`
- `grb-sens template`
- `grb-sens validate --config grb_sensitivity.yaml`
- `grb-sens run --config grb_sensitivity.yaml --dry-run`

## Example terminal outputs

`grb-sens --user-help` starts with:

```text
GRB Sensitivity Calculator

Purpose
  grb-sens is an educational command-line tool for setting up Band (2003)-style
  gamma-ray burst detector sensitivity calculations.

Quick start
  grb-sens init
  grb-sens validate --config grb_sensitivity.yaml
  grb-sens run --config grb_sensitivity.yaml --dry-run
```

`grb-sens validate --config examples/example_curve.yaml` prints:

```text
Configuration is valid: examples/example_curve.yaml
```

`grb-sens run --config examples/example_curve.yaml --dry-run` prints a summary
including mode, Band parameters, response quantity, detector area, trigger band,
accumulation time, and the note that Stage 1 is a mock validation summary.

## Interactive YAML creation flow

When `grb-sens` is run with no subcommand and no `grb_sensitivity.yaml` exists,
the CLI asks:

```text
No configuration file was found in the current directory.
Would you like to create a new grb_sensitivity.yaml interactively? [Y/n]
```

The wizard then requires the student to choose `response.quantity`:

```text
Select detector response quantity:
  1) efficiency          - CSV value is dimensionless detection efficiency
  2) effective_area_cm2  - CSV value already includes collecting area
Enter choice [1/2]:
```

If `grb_sensitivity.yaml` already exists and the user chooses to create a new
one, the old file is renamed to `grb_sensitivity_YYYYMMDD_HHMMSS.yaml.bak`
before the new file is written.

## Human review checklist

- Check whether the command names are understandable to students.
- Check whether the generated YAML template is readable and not too terse.
- Check whether the required `response.quantity` prompt is clear.
- Check whether `--user-help` contains enough normal-use guidance.
- Check whether `--developer-help` gives enough orientation for reading the code.
- Confirm that the Stage 1 dry-run wording does not imply scientific validation.
