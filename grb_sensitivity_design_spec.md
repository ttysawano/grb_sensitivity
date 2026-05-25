# GRB Sensitivity Calculator v0.1 Design Specification

## 1. Purpose

This document defines the v0.1 design of a small educational Python command-line tool for calculating gamma-ray burst (GRB) detector sensitivity using the formulation of Band (2003).

The tool is intended for students and early-stage developers. The source code should therefore be written not only to compute correct results, but also to help readers learn the physics and the numerical method directly from the implementation.

The program name used in this specification is:

```text
grb-sens
```

The Python package name used in this specification is:

```text
grb_sensitivity
```

The v0.1 tool shall support two main calculation modes:

1. `curve`
   - Compute a Band (2003)-style threshold peak photon flux curve.
   - The output is threshold peak photon flux as a function of GRB `Epeak`.

2. `significance`
   - Compute the detection significance of a specific GRB spectrum and peak flux for a given detector setup.

The default calculation mode shall be `curve`.

---

## 2. Scientific Basis

### 2.1 Band (2003) sensitivity formulation

The primary reference formulation is Band (2003), "Comparison of the Gamma-Ray Burst Sensitivity of Different Detectors".

The central idea is to express the detector threshold in a detector-independent reference quantity:

```text
F_T = threshold peak photon flux integrated over [E_l, E_h]
```

The default reference band is:

```text
E_l = 1 keV
E_h = 1000 keV
```

The detector, however, triggers over its own trigger band:

```text
E_1 <= E <= E_2
```

The default trigger band for v0.1 is:

```text
E_1 = 10 keV
E_2 = 1000 keV
```

The trigger significance is computed by comparing source counts with the square root of background counts:

```text
significance = source_counts / sqrt(background_counts)
```

This is the Gaussian approximation used in the v0.1 implementation.

Poisson exact significance, image-domain triggers, and orbital background variation are out of scope for v0.1.

### 2.2 Band spectrum

The GRB photon spectrum is the Band function:

```text
N(E) = dN/dE  [ph cm^-2 s^-1 keV^-1]
```

The model parameters are:

```text
N0          normalization
alpha       low-energy photon index
beta        high-energy photon index
Epeak       peak energy of E^2 N(E)
Epivot      pivot energy, default 100 keV
```

The default spectral parameters for v0.1 are:

```text
alpha = -1.0
beta  = -2.5
Epivot = 100 keV
```

The e-folding energy is:

```text
E_0 = Epeak / (alpha + 2)
```

The spectral break energy is:

```text
E_b = (alpha - beta) * E_0
```

Validation rules:

```text
alpha > -2
alpha > beta
Epeak > 0
Epivot > 0
N0 > 0 when explicitly supplied
```

### 2.3 CXB model

The default cosmic X-ray background (CXB) model shall be `moretti2009`.

The implementation shall use the two smoothly joined power-law model (2SJPL) from Moretti et al. (2009), Eq. (4):

```text
E^2 dN/dE = C * E^2 / [ (E/E_B)^Gamma1 + (E/E_B)^Gamma2 ]
```

Equivalently:

```text
dN/dE = C / [ (E/E_B)^Gamma1 + (E/E_B)^Gamma2 ]
```

where:

```text
C       = 0.109
Gamma1  = 1.40
Gamma2  = 2.88
E_B     = 29.0 keV
```

The formula in Moretti et al. is expressed per square degree. Internally, this tool shall use steradian units:

```text
ph cm^-2 s^-1 sr^-1 keV^-1
```

Therefore, the conversion shall be:

```text
I_sr(E) = I_deg2(E) * (180/pi)^2
```

because:

```text
1 sr = (180/pi)^2 deg^2
```

The nominal validity range of the built-in `moretti2009` model is:

```text
10 keV <= E <= 200 keV
```

The v0.1 policy outside this nominal range shall be:

```text
below_valid_range_policy: truncate_with_warning
above_valid_range_policy: evaluate_with_warning
```

This means:

- If the requested CXB integration range extends below 10 keV, the lower part is truncated and a warning is printed.
- If the requested CXB integration range extends above 200 keV, the formula is still evaluated, but a warning is printed.
- The warning shall clearly state that high-energy use of this model is an extrapolation.

A table-based CXB/background model shall be reserved in the configuration schema but does not need to be fully implemented beyond a skeleton in v0.1 unless time permits.

### 2.4 CXB consistency checks

The implementation shall include tests or developer utilities to verify that the `moretti2009` model is implemented with the correct units.

At minimum, the following consistency check shall be implemented:

1. Integrate the `moretti2009` model over 2-10 keV.
2. Convert from photon flux to energy flux using:

```text
1 keV = 1.602176634e-9 erg
```

3. Verify that the result is close to:

```text
2.21e-11 erg cm^-2 s^-1 deg^-2
```

This number is the 2-10 keV energy flux reported for the 2SJPL model by Moretti et al. (2009).

A second developer check should compare the result qualitatively with HEAO-1 / Gruber et al. (1999):

- Moretti et al. report that their model is roughly 30% higher than HEAO-1/G99 in the 2-10 keV band.
- The same paper states that the model is marginally consistent with HEAO-1 at energies higher than about 20 keV, at roughly the 10% level.

This check is not a strict unit test in v0.1 because the Gruber model is not required as a built-in model. It may be implemented as a documented numerical comparison if the G99 formula is added later.

---

## 3. Detector Response Model

### 3.1 Response CSV

The detector response shall be supplied as a CSV file.

Default path:

```text
detector_response.csv
```

The CSV may represent either:

1. `efficiency`
   - Dimensionless detector efficiency.
   - The geometric detector area is supplied separately.

2. `effective_area_cm2`
   - Effective collecting area in cm^2.
   - This is treated as pre-mask effective area unless explicitly configured otherwise.

The `response.quantity` field has no default. The user must choose either `efficiency` or `effective_area_cm2`.

### 3.2 Column specification

The energy and value columns may be specified either by column name or by 1-based column number.

Examples:

```yaml
energy_column: 1
value_column: 2
```

or:

```yaml
energy_column: energy_keV
value_column: efficiency
```

Column numbers are 1-based to match the way students often count columns in spreadsheet software.

The program shall internally convert 1-based column numbers to 0-based indices when using pandas or Python lists.

### 3.3 Positive-value requirement

Because v0.1 uses log-log interpolation, the response CSV must satisfy:

```text
energy_keV > 0
response_value > 0
```

Zero or negative values shall raise a validation error in v0.1.

A future version may add an explicit zero-value policy, but that is out of scope for v0.1.

### 3.4 Log-log interpolation

The detector response shall be interpolated in log-log space.

For two tabulated points:

```text
(E_a, y_a), (E_b, y_b)
```

the interpolation is linear in:

```text
log(E), log(y)
```

The default interpolation mode is:

```text
loglog
```

### 3.5 Extrapolation

The default extrapolation mode is:

```text
powerlaw_with_warning
```

This means the endpoint slope in log-log space is used to extrapolate outside the tabulated energy range, and a warning is printed.

This warning is important because students may accidentally request a trigger band much wider than the response CSV range.

---

## 4. Detector Geometry and Mask Model

### 4.1 Default detector parameters

The default detector parameters are:

```yaml
detector:
  name: grb_detector
  geometric_area_cm2: 100.0
  active_fraction: 1.0
  aperture_solid_angle_sr: 1.0
```

### 4.2 Internal area convention

The core calculation shall use:

```text
A_eff_pre_mask(E)
```

This is the collecting area before applying the coded-mask open fraction.

For `response.quantity: efficiency`:

```text
A_eff_pre_mask(E) = A * f_det * eta(E)
```

where:

```text
A      = geometric area [cm^2]
f_det  = active detector-plane fraction
eta(E) = detector efficiency
```

For `response.quantity: effective_area_cm2`:

```text
A_eff_pre_mask(E) = effective_area_cm2(E)
```

By default, `effective_area_cm2(E)` is assumed to include the detector active fraction if it came from a simulation or calibration curve. This should be explicit in YAML:

```yaml
effective_area_includes_active_fraction: true
effective_area_includes_mask: false
```

### 4.3 Mask open fraction

The default mask settings are:

```yaml
detector:
  mask:
    open_fraction: 1.0
    response_includes_mask: false
    apply_to_source: true
    apply_to_cxb: true
```

By default, the response CSV does not include the coded mask open fraction.

The source counts use:

```text
source_counts = Delta_t * f_mask_source * integral[A_eff_pre_mask(E) * N(E) dE]
```

The sky CXB background counts use:

```text
cxb_counts = Delta_t * f_mask_cxb * Omega * integral[A_eff_pre_mask(E) * N_B(E) dE]
```

where:

```text
Omega = aperture solid angle [sr]
N_B(E) = CXB photon intensity [ph cm^-2 s^-1 sr^-1 keV^-1]
```

If `response_includes_mask: true`, the implementation must avoid double-counting the mask. It should either set the effective mask factor to unity or raise a clear validation warning if the configuration is ambiguous.

---

## 5. Background Model

### 5.1 Total background

The v0.1 background model is:

```text
background_counts_total = background_counts_cxb + background_counts_internal
```

### 5.2 CXB background

If CXB is enabled:

```text
background_counts_cxb =
    Delta_t * f_mask_cxb * Omega *
    integral_{E_1}^{E_2} A_eff_pre_mask(E) * N_B(E) dE
```

The default CXB settings are:

```yaml
background:
  cxb:
    enabled: true
    model: moretti2009
    nominal_valid_energy_range_keV: [10.0, 200.0]
    below_valid_range_policy: truncate_with_warning
    above_valid_range_policy: evaluate_with_warning
```

### 5.3 Internal background

For v0.1, the primary internal background input is a trigger-band-integrated count rate:

```text
R_int_cps [counts s^-1]
```

The default is:

```yaml
background:
  internal:
    mode: trigger_band_rate
    rate_cps: 0.0
```

The corresponding internal background counts are:

```text
background_counts_internal = R_int_cps * Delta_t
```

A skeleton for a differential internal background may be included:

```yaml
background:
  internal:
    mode: differential_rate
    rate_unit: counts_s_cm2_keV
```

but full implementation is not required in v0.1.

Important code comment requirement:

```text
In Band (2003), B_int is written as a differential internal
background term. In this v0.1 implementation, the main
user-facing internal background input is R_int_cps, the count
rate already integrated over the trigger band [E_1, E_2].
```

---

## 6. Numerical Integration

### 6.1 Integration method

v0.1 shall use a log-spaced energy grid and trapezoidal integration.

Default numerical settings:

```yaml
numerics:
  integration_grid:
    num: 4096
    spacing: log
```

The implementation should use a simple and readable method:

```python
E_grid = np.logspace(np.log10(E_min), np.log10(E_max), n_grid)
integral = np.trapezoid(y_grid, E_grid)
```

`np.trapezoid` is preferred. If compatibility with older NumPy versions is needed, `np.trapz` may be used with a comment.

### 6.2 Curve grid

For `curve` mode, the default Epeak grid is:

```yaml
curve:
  epeak_grid_keV:
    min: 10.0
    max: 10000.0
    num: 256
    spacing: log
```

---

## 7. Core Calculations

### 7.1 Source counts

For a normalized Band spectrum `N(E)`:

```text
source_counts =
    Delta_t * f_mask_source *
    integral_{E_1}^{E_2} A_eff_pre_mask(E) * N(E) dE
```

### 7.2 Background counts

```text
background_counts_total =
    background_counts_cxb + background_counts_internal
```

### 7.3 Significance

```text
significance_sigma = source_counts / sqrt(background_counts_total)
```

If `background_counts_total <= 0`, the implementation shall raise a clear error unless the user explicitly requests a special no-background diagnostic mode. Such a diagnostic mode is not required in v0.1.

### 7.4 Threshold peak photon flux

For `curve` mode, the tool computes the threshold photon flux `F_T` over the reference band:

```text
E_l = 1 keV
E_h = 1000 keV
```

The default threshold significance is:

```text
sigma_0 = 8.0
```

For each `Epeak`, the Band normalization shall be chosen so that:

```text
significance_sigma = sigma_0
```

The output `F_T` is then:

```text
F_T = integral_{E_l}^{E_h} N_T(E) dE
```

where `N_T(E)` is the threshold-normalized Band spectrum.

The implementation may compute `F_T` either by direct scaling from a trial normalization or by the analytic ratio form equivalent to Band (2003), Eq. (5).

For educational readability, the code should explicitly show the following quantities:

```text
source_counts_per_N0
background_counts_total
scale_to_threshold
F_T
```

---

## 8. Configuration YAML

### 8.1 Default YAML structure

The tool shall generate a commented YAML file similar to:

```yaml
version: 0.1

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
    mode: trigger_band_rate
    rate_cps: 0.0

numerics:
  integration_grid:
    num: 4096
    spacing: log

output:
  csv: sensitivity_curve.csv
  plot: sensitivity_curve.png
```

### 8.2 Required fields

The following fields are required:

```text
version
mode
spectrum.model
spectrum.alpha
spectrum.beta
detector.response.path
detector.response.quantity
detector.response.energy_column
detector.response.value_column
detector.trigger.energy_band_keV
```

If `response.quantity == efficiency`, then:

```text
detector.geometric_area_cm2
```

is required.

If CXB is enabled, then:

```text
detector.aperture_solid_angle_sr
```

is required.

---

## 9. Interactive CLI Wizard

### 9.1 Basic behavior

If no configuration file is found in the current directory, running:

```bash
grb-sens
```

shall prompt the user:

```text
No configuration file was found in the current directory.
Would you like to create a new grb_sensitivity.yaml interactively? [Y/n]
```

The default file name is:

```text
grb_sensitivity.yaml
```

If the file exists, running:

```bash
grb-sens
```

shall prompt:

```text
Found configuration file: grb_sensitivity.yaml
Use this configuration and run the calculation? [Y/n]
```

If the user answers `n`, the tool shall ask whether to create a new configuration.

If a new configuration is created while an old one exists, the old file shall be renamed with a timestamp:

```text
grb_sensitivity_YYYYMMDD_HHMMSS.yaml.bak
```

The existing file must never be overwritten silently.

### 9.2 Response quantity must be chosen

The wizard shall not provide a default for `response.quantity`.

It shall display:

```text
Select detector response quantity:
  1) efficiency          - CSV value is dimensionless detection efficiency
  2) effective_area_cm2  - CSV value already includes collecting area
Enter choice [1/2]:
```

Invalid input shall trigger re-prompting.

### 9.3 Default answers

Most other questions shall provide defaults and accept Enter.

Examples:

```text
Detector name [grb_detector]:
Response CSV path [detector_response.csv]:
Energy column name or 1-based column number [1]:
Value column name or 1-based column number [2]:
Geometric area [cm^2] [100.0]:
Trigger lower energy E_1 [keV] [10.0]:
Trigger upper energy E_2 [keV] [1000.0]:
Accumulation time Delta_t [s] [1.0]:
Threshold significance sigma_0 [8.0]:
Internal background rate in trigger band [counts/s] [0.0]:
Aperture solid angle Omega [sr] [1.0]:
Band alpha [-1.0]:
Band beta [-2.5]:
```

The wizard shall avoid overly friendly extra branches that are not required for v0.1. For example, it shall not ask a special question such as "Do you want to extend to MeV energies?" because the user can directly edit the trigger band.

### 9.4 Non-interactive environment

If no configuration is found and stdin is not a TTY, the program shall not wait for input.

It shall exit with a clear message:

```text
No configuration file was found, and interactive mode is not available.
Run `grb-sens init` in a terminal, or specify `--config path/to/config.yaml`.
```

---

## 10. Command-Line Interface

### 10.1 Required commands

The following commands shall be supported:

```bash
grb-sens
grb-sens init
grb-sens validate --config grb_sensitivity.yaml
grb-sens run --config grb_sensitivity.yaml
grb-sens run --config grb_sensitivity.yaml --dry-run
grb-sens template
```

### 10.2 Help and manual output

The tool shall provide both user-facing and developer-facing help text from the command line.

Required options or subcommands:

```bash
grb-sens --help
grb-sens --user-help
grb-sens --developer-help
grb-sens help user
grb-sens help developer
```

Aliases may be implemented, but at least `--user-help` and `--developer-help` must work.

#### User help

`--user-help` shall print a plain-text manual for normal users.

It shall include:

- Purpose of the tool.
- Quick start.
- How to create a YAML file interactively.
- How to run a sensitivity curve.
- How to run a known-GRB significance calculation.
- Explanation of required input files.
- Explanation of the response CSV format.
- Explanation of major YAML fields.
- Common warnings and what they mean.
- Example commands.

#### Developer help

`--developer-help` shall print a plain-text guide for developers and students reading the code.

It shall include:

- Package layout.
- Physics modules and their roles.
- Mapping between Band (2003) notation and Python variable names.
- Unit conventions.
- Where to find the core calculation.
- How to run tests.
- How to add a new background model.
- How to add a new spectrum model.
- How to add a new output column.
- Code-comment policy.

Both help outputs shall be plain text and shall not require internet access.

---

## 11. Output Files

### 11.1 Curve mode CSV

The curve mode output CSV shall contain at least:

```text
epeak_keV
threshold_photon_flux_ph_cm2_s
threshold_energy_flux_erg_cm2_s
source_counts_at_threshold
background_counts_total
background_counts_cxb
background_counts_internal
trigger_energy_min_keV
trigger_energy_max_keV
sigma0
```

### 11.2 Significance mode CSV

The significance mode output CSV shall contain at least:

```text
grb_name
alpha
beta
epeak_keV
peak_flux_ph_cm2_s
peak_flux_band_min_keV
peak_flux_band_max_keV
source_counts
background_counts_total
background_counts_cxb
background_counts_internal
significance_sigma
detected
```

where:

```text
detected = significance_sigma >= threshold_sigma
```

### 11.3 Plot output

For `curve` mode, the tool shall produce a PNG plot if `output.plot` is set.

The default plot file is:

```text
sensitivity_curve.png
```

The plot shall use:

```text
x-axis: Epeak [keV]
y-axis: threshold photon flux [ph cm^-2 s^-1]
```

Both axes should be logarithmic by default.

---

## 12. Variable Naming Policy

The core calculation should use variable names close to Band (2003), while the external API and YAML should use descriptive names.

### 12.1 Band spectrum

| Paper symbol | Preferred Python name | Meaning |
|---|---|---|
| E | `E_keV` | Photon energy |
| N(E) | `N_E` or `dnde` | Photon spectrum |
| N0 | `N0` | Band normalization |
| alpha | `alpha` | Low-energy photon index |
| beta | `beta` | High-energy photon index |
| E_p | `E_p` or `epeak_keV` | Peak energy |
| E_0 | `E_0` or `e0_keV` | E-folding energy |
| E_b | `E_b` or `ebreak_keV` | Break energy |
| E_pivot | `E_pivot` or `epivot_keV` | Pivot energy |

Inside short functions implementing equations, `E_p`, `E_0`, and `E_b` are encouraged.

In public interfaces, use `epeak_keV`, `e0_keV`, and `ebreak_keV`.

### 12.2 Flux and trigger bands

| Paper symbol | Preferred Python name | Meaning |
|---|---|---|
| E_l | `E_l` | Reference flux lower bound |
| E_h | `E_h` | Reference flux upper bound |
| E_1 | `E_1` | Trigger lower bound |
| E_2 | `E_2` | Trigger upper bound |
| F_T | `F_T` | Threshold peak photon flux |
| Delta t | `Delta_t` or `dt_s` | Accumulation time |
| sigma_0 | `sigma_0` | Threshold significance |

### 12.3 Detector and background

| Paper symbol | Preferred Python name | Meaning |
|---|---|---|
| A | `A` | Geometric area |
| f_det | `f_det` | Active fraction |
| f_mask | `f_mask` | Mask open fraction |
| eta(E) | `eta_E` | Efficiency |
| Omega | `Omega` | Aperture solid angle |
| B(E) | `B_E` | Differential background rate |
| B_int | `B_int` | Internal background term |
| N_B(E) | `N_B_E` | Diffuse sky background photon intensity |
| R_int | `R_int_cps` | Trigger-band internal background rate |

---

## 13. Validation Rules

The program shall validate the following:

```text
mode in ["curve", "significance"]
response.quantity in ["efficiency", "effective_area_cm2"]
alpha > -2
alpha > beta
E_l > 0
E_h > E_l
E_1 > 0
E_2 > E_1
Epeak > 0
threshold_sigma > 0
accumulation_time_s > 0
geometric_area_cm2 > 0 when required
active_fraction > 0
active_fraction <= 1 unless explicitly allowed
mask.open_fraction > 0
mask.open_fraction <= 1 unless explicitly allowed
aperture_solid_angle_sr > 0 if CXB is enabled
CSV energy values > 0
CSV response values > 0
```

Validation errors shall be written in plain English and should suggest how to fix the issue.

---

## 14. Package Layout

The recommended package layout is:

```text
grb_sensitivity/
  __init__.py
  cli.py
  config_schema.py
  config_io.py
  wizard.py
  spectra.py
  response.py
  background.py
  detector.py
  sensitivity.py
  output.py
  help_text.py

examples/
  detector_response_efficiency.csv
  detector_response_effective_area.csv
  example_curve.yaml
  example_significance.yaml

tests/
  test_band_spectrum.py
  test_response.py
  test_background_moretti2009.py
  test_sensitivity.py
  test_config_validation.py
  test_cli_wizard.py
```

---

## 15. Dependency Policy

The v0.1 implementation should keep dependencies modest.

Required:

```text
numpy
pandas
matplotlib
pyyaml or ruamel.yaml
```

Recommended for tests:

```text
pytest
```

`scipy` is not required for v0.1 because numerical integration can be implemented using NumPy trapezoidal integration.

For commented YAML generation:

- `ruamel.yaml` may be used if convenient.
- Alternatively, a plain template string may be used to produce a commented YAML file.
- The generated YAML should be readable as a teaching document.

---

## 16. Code Comment Policy

The source code shall be written as educational code.

Requirements:

1. Core physics functions shall include comments identifying the relevant equation or concept.
2. Units shall be written in comments near important variables.
3. `counts`, `rate`, `photon_flux`, and `energy_flux` shall be clearly distinguished.
4. The Band (2003) notation shall be referenced in comments where helpful.
5. The Moretti et al. (2009) CXB model shall include a comment explaining the deg^-2 to sr^-1 conversion.
6. Approximations shall be explicitly noted.
7. The code should prefer clarity over overly compact implementation.

Example comment style:

```python
# Band (2003) Eq. (5) converts a count-rate threshold in the
# detector trigger band [E_1, E_2] into a threshold photon flux
# F_T in the reference band [E_l, E_h]. The Band normalization
# cancels in the ratio of spectral integrals.
```

Another example:

```python
# Moretti et al. (2009) Eq. (4) is written per square degree.
# The detector background calculation uses Omega in steradians,
# so we convert the CXB intensity from deg^-2 to sr^-1.
```

---

## 17. v0.1 Out-of-Scope Items

The following are intentionally out of scope for v0.1:

```text
Poisson exact significance
Imaging-trigger significance
Detector response matrix with off-diagonal redistribution
Time-dependent background
Orbital background variation
Earth albedo background
Particle background modeling beyond a constant trigger-band rate
Band + high-energy power-law GRB model
Redshift and luminosity calculations
Cosmological k-corrections
LAT-LLE full detector-response treatment
GUI
```

However, the YAML structure may include report bands such as 30-100 MeV to prepare for future LAT-LLE-related extensions.

---

## 18. Minimum Acceptance Criteria

The v0.1 implementation is acceptable when:

1. `grb-sens --help` works.
2. `grb-sens --user-help` works.
3. `grb-sens --developer-help` works.
4. `grb-sens init` creates a commented YAML file.
5. `grb-sens validate --config grb_sensitivity.yaml` validates a generated configuration.
6. `grb-sens run --config examples/example_curve.yaml` produces a curve CSV.
7. `grb-sens run --config examples/example_significance.yaml` produces a significance CSV.
8. The Moretti 2009 CXB implementation passes the 2-10 keV energy-flux consistency check.
9. The Band spectrum implementation passes basic normalization and integration tests.
10. The detector response interpolation rejects zero and negative values.
11. The code contains educational comments in the core physics functions.
