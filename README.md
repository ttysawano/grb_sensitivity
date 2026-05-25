# GRB Sensitivity Calculator

`grb-sens` is an educational Python command-line tool for gamma-ray burst
(GRB) detector sensitivity calculations using a Band (2003)-style formulation.
It is written for students and early-stage developers, so the source code tries
to show the physics quantities, units, and numerical approximations directly.

The package name is `grb_sensitivity`; the command-line program is `grb-sens`.

## What The Tool Does

`grb-sens` supports two v0.1 calculation modes:

- `curve`: compute a threshold peak photon flux curve as a function of GRB
  `Epeak`.
- `significance`: compute the Gaussian detection significance for one GRB
  spectrum and peak flux.

The threshold flux is reported in the reference photon-flux band
`[E_l, E_h] = [1, 1000] keV`. The detector trigger uses its configured trigger
band `[E_1, E_2]`, which defaults to `[10, 1000] keV`.

## Scientific Scope And Limitations

v0.1 intentionally uses a limited educational model:

- Trigger significance is the Gaussian approximation `S / sqrt(B)`.
- The GRB spectrum is the Band function.
- Detector response is a one-dimensional CSV curve, not a full response matrix.
- Detector response interpolation is log-log and requires positive values.
- Sky background uses the built-in Moretti et al. (2009) CXB model.
- Particle/internal background is only a user-supplied trigger-band count rate.
- The default internal background `rate_cps: 0.0` is a mathematical default,
  not a realistic detector background.
- Moretti et al. (2009) is primarily an X-ray/hard-X-ray CXB model. Use above 200 keV is
  allowed but emits an extrapolation warning.

Out of scope for v0.1: Poisson exact significance, image-domain triggers, full
detector redistribution matrices, orbital background variation, Earth albedo,
particle background modeling beyond a constant count rate, cosmological
corrections.

## Installation For Local Development

From the repository root:

```bash
python -m pip install --user .
```

For editable development, use a virtual environment with a modern `pip`, then:

```bash
python -m pip install -e ".[test]"
```

The test suite uses `pytest`:

```bash
pytest
```

## Quick Start

```bash
grb-sens --help
grb-sens --user-help
grb-sens validate --config examples/example_curve.yaml
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

To see the configuration summary without writing outputs:

```bash
grb-sens run --config examples/example_curve.yaml --dry-run
```

## Create A YAML Configuration Interactively

Run:

```bash
grb-sens
```

If no `grb_sensitivity.yaml` exists in the current directory, the CLI asks
whether to create one. The wizard requires one non-default choice:

```text
response.quantity:
  efficiency          CSV values are dimensionless efficiency
  effective_area_cm2  CSV values are already collecting area in cm^2
```

`grb-sens init` also creates a configuration interactively. Existing
configuration files are not overwritten silently; they are backed up with a
timestamp if the wizard creates a replacement.

## Run Curve Mode

Curve mode computes threshold photon flux versus `Epeak`:

```bash
grb-sens run --config examples/example_curve.yaml
```

The bundled example writes:

- `examples/output/example_curve.csv`
- `examples/output/example_curve.png`

The plot uses `Epeak [keV]` on the x-axis and threshold photon flux
`[ph cm^-2 s^-1]` on the y-axis, with logarithmic axes.

## Run Significance Mode

Significance mode computes source counts, background counts, and Gaussian
significance for one configured GRB:

```bash
grb-sens run --config examples/example_significance.yaml
```

The bundled example writes:

- `examples/output/example_significance.csv`

## Response CSV Format

The detector response CSV must contain:

- one column with photon energy in keV
- one column with either efficiency or effective area

Columns can be selected by 1-based column number:

```yaml
energy_column: 1
value_column: 2
```

or by column name:

```yaml
energy_column: energy_keV
value_column: efficiency
```

Because v0.1 uses log-log interpolation, all response energies and response
values must be strictly positive. Zero or negative values are rejected.

## `efficiency` Versus `effective_area_cm2`

Use:

```yaml
response:
  quantity: efficiency
```

when the CSV value is dimensionless detector efficiency `eta(E)`. The code uses:

```text
A_eff_pre_mask(E) = geometric_area_cm2 * active_fraction * eta(E)
```

Use:

```yaml
response:
  quantity: effective_area_cm2
```

when the CSV value is already effective collecting area in cm^2. By default this
is interpreted as pre-mask area, with the coded-mask factor applied separately.

## Major YAML Fields

- `mode`: `curve` or `significance`.
- `spectrum`: Band model parameters `alpha`, `beta`, and `epivot_keV`.
- `flux.reference_band_keV`: photon-flux reporting band, default `[1, 1000]`.
- `curve.epeak_grid_keV`: `Epeak` grid for curve mode.
- `grb`: GRB name, `epeak_keV`, and peak flux for significance mode.
- `detector.response`: CSV path, response quantity, and column selection.
- `detector.trigger`: trigger band, accumulation time, threshold sigma.
- `detector.mask`: coded-mask open fraction and response-mask convention.
- `background.cxb`: Moretti et al. (2009) CXB settings and validity-range policies.
- `background.internal.rate_cps`: trigger-band internal background rate.
- `numerics.integration_grid.num`: log-grid size for trapezoidal integration.
- `output.csv` and `output.plot`: output paths relative to the YAML file.

## Output CSV Columns

Curve output includes:

- `epeak_keV`
- `threshold_photon_flux_ph_cm2_s`
- `threshold_energy_flux_erg_cm2_s`
- `source_counts_at_threshold`
- `background_counts_total`
- `background_counts_cxb`
- `background_counts_internal`
- `trigger_energy_min_keV`
- `trigger_energy_max_keV`
- `sigma0`

Significance output includes:

- `grb_name`
- `alpha`, `beta`, `epeak_keV`
- `peak_flux_ph_cm2_s`
- `peak_flux_band_min_keV`, `peak_flux_band_max_keV`
- `source_counts`
- `background_counts_total`
- `background_counts_cxb`
- `background_counts_internal`
- `significance_sigma`
- `detected`

## Common Warnings

Moretti et al. (2009) warning above 200 keV:

```text
The Moretti et al. (2009) CXB model is being evaluated above 200 keV. This is an extrapolation.
```

This means the configured trigger band extends beyond the nominal validity
range of the built-in CXB model. The example trigger band is `10-1000 keV`, so
this warning is expected for the bundled examples.

Detector response extrapolation warnings mean the trigger or integration band
extends beyond the tabulated response CSV range. Review the CSV energy range or
choose a narrower trigger band.

## Example Commands

```bash
grb-sens template
grb-sens init
grb-sens validate --config examples/example_curve.yaml
grb-sens run --config examples/example_curve.yaml --dry-run
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

## Developer Orientation

Start with these files:

- `grb_sensitivity/cli.py`: command-line entry point.
- `grb_sensitivity/config_schema.py`: YAML defaults and validation.
- `grb_sensitivity/config_io.py`: YAML loading and template generation.
- `grb_sensitivity/wizard.py`: interactive YAML creation.
- `grb_sensitivity/spectra.py`: Band spectrum and flux integrations.
- `grb_sensitivity/response.py`: response CSV loading and log-log interpolation.
- `grb_sensitivity/background.py`: Moretti et al. (2009) CXB and internal background.
- `grb_sensitivity/detector.py`: detector area and mask conventions.
- `grb_sensitivity/sensitivity.py`: counts, significance, and threshold flux.
- `grb_sensitivity/output.py`: CSV/plot writing and CLI run execution.

Run the full suite before reporting changes:

```bash
pytest
```
