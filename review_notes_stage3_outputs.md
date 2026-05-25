# Stage 3 Output Review Notes

## How Outputs Were Generated

The Stage 3 CLI was connected to the Stage 2 physics engine. The checked-in
example outputs were generated from the example YAML files:

```bash
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

The dry-run summary mode remains available and does not write output files:

```bash
grb-sens run --config examples/example_curve.yaml --dry-run
```

## Generated Files

- `examples/output/example_curve.csv`
- `examples/output/example_curve.png`
- `examples/output/example_significance.csv`

## Expected Qualitative Behavior

The curve output reports the threshold photon flux over the reference
1-1000 keV band as a function of `Epeak`. For the bundled toy detector response,
the curve should be smooth on log-log axes. It is an educational numerical
sanity example, not a validated instrument performance claim.

The significance output is one row for `example_grb`, containing source counts,
CXB/internal background counts, Gaussian `S/sqrt(B)` significance, and a
`detected` flag.

## Warnings Emitted

Both example runs use the default trigger band 10-1000 keV. The built-in
Moretti 2009 CXB model has nominal validity through 200 keV, so the CLI emits:

```text
The Moretti 2009 CXB model is being evaluated above 200 keV. This is an extrapolation.
```

This warning is expected for the current example configuration.

## Human Numerical Sanity Checklist

- Confirm the sensitivity curve is smooth and not obviously discontinuous.
- Confirm threshold flux values are finite and positive.
- Confirm `source_counts_at_threshold / sqrt(background_counts_total)` is close to `sigma0`.
- Confirm `background_counts_total = background_counts_cxb + background_counts_internal`.
- Confirm the significance example has finite positive counts and a sensible `detected` flag.
- Confirm the high-energy CXB extrapolation warning is acceptable for the configured trigger band.

Stage 3 connects the CLI to the physics engine and produces example outputs. It
does not attempt final documentation polish; that remains Stage 4.
