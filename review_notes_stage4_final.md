# Stage 4 Final Review Notes

## Final Implemented Features

- Package skeleton and CLI commands: `--help`, `--user-help`, `--developer-help`, `help user`, `help developer`, `init`, `template`, `validate`, and `run`.
- Interactive YAML creation with required `response.quantity` selection and timestamped backup behavior.
- Configuration loading and validation with clearer student-facing error messages.
- Band spectrum evaluation, `E_0`, `E_b`, photon flux integration, energy flux integration, and renormalization.
- Detector response CSV loading by name or 1-based column number.
- Positive-value enforcement for log-log response interpolation.
- Power-law response extrapolation with warnings.
- Moretti et al. (2009) CXB model using the corrected per-steradian convention.
- Source counts, CXB/internal background counts, total background, Gaussian significance, and threshold flux.
- Real curve-mode and significance-mode CLI execution from YAML.
- Curve CSV and PNG output.
- Significance CSV output.
- Example output bundle under `examples/output/`.
- Stage review notes for Stages 1 through 4.

## Final Command Examples

```bash
grb-sens --help
grb-sens --user-help
grb-sens --developer-help
grb-sens template
grb-sens validate --config examples/example_curve.yaml
grb-sens run --config examples/example_curve.yaml --dry-run
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
pytest
```

## Reproduce Example Outputs

From the repository root:

```bash
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

Expected files:

- `examples/output/example_curve.csv`
- `examples/output/example_curve.png`
- `examples/output/example_significance.csv`

## Test Results

Final Stage 4 test command:

```bash
pytest
```

Expected result at Stage 4 completion:

```text
46 passed
```

## Human Educational Readability Checklist

- Read `README.md` as a student and confirm the quick start is enough to run examples.
- Check `grb-sens --user-help` for normal user clarity.
- Check `grb-sens --developer-help` for source-code orientation.
- Inspect core comments in `spectra.py`, `response.py`, `background.py`, `detector.py`, and `sensitivity.py`.
- Confirm validation errors explain how to fix common YAML and CSV mistakes.
- Confirm output CSV column names are understandable and documented.

## Scientific Limitations Of v0.1

- Uses Gaussian `S/sqrt(B)` significance only.
- Does not implement Poisson exact significance.
- Does not model image-domain triggers.
- Does not model full detector response matrices or energy redistribution.
- Uses a one-dimensional detector response CSV.
- Does not model time-dependent or orbital background variation.
- Does not model particle background beyond a constant trigger-band count rate.
- The default internal background rate of `0.0 counts/s` is a mathematical default, not a realistic detector background.
- The Moretti et al. (2009) CXB model is primarily intended for the X-ray/hard-X-ray band.
- Use above 200 keV is allowed but warned as extrapolation.

## Known Warnings And Meanings

- Moretti et al. (2009) above 200 keV: the CXB model is being extrapolated beyond its nominal validity range.
- Moretti et al. (2009) below 10 keV: the CXB integral is truncated below the nominal range.
- Detector response extrapolation: the calculation requested energies outside the response CSV range.
- Zero/negative response CSV values: log-log interpolation cannot use those values.

## Intentionally Out Of Scope

- PDF reference-paper bundling.
- GUI.
- Full instrument calibration or response matrices.
- New scientific models beyond the v0.1 Band spectrum and Moretti et al. (2009) CXB.
- Documentation polish beyond README/help/review-note completion.

## Suggested Next Steps After v0.1

- Have a domain reviewer compare the Band and Moretti equations against the source.
- Add measured or simulated internal background examples for a real instrument.
- Add optional output metadata describing warnings and configuration provenance.
- Add a table-based background model if needed for instrument-specific studies.
- Add more hand-check examples with simple analytic response/background cases.
