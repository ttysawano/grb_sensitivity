# GRB Sensitivity Calculator

`grb-sens` is an educational command-line skeleton for a Band (2003)-style
gamma-ray burst detector sensitivity calculator.

Stage 1 implements the project layout, configuration loading and validation,
interactive YAML creation skeleton, help text, examples, and dry-run CLI
behavior. The real physics calculation is intentionally left for later stages.

## Quick Start

```bash
grb-sens template
grb-sens validate --config examples/example_curve.yaml
grb-sens run --config examples/example_curve.yaml --dry-run
```

Run `grb-sens --user-help` for normal usage notes and
`grb-sens --developer-help` for a guide to the package layout.
