# Codex Implementation Instructions for `grb-sens` v0.1

## 0. Purpose of This Document

This document gives staged implementation instructions for Codex or another coding agent.

The implementation target is the educational Python package and command-line tool:

```text
Package name: grb_sensitivity
CLI command: grb-sens
```

The scientific and software requirements are defined in:

```text
grb_sensitivity_design_spec.md
```

Codex must read and follow the design specification first. This document explains the implementation order, review checkpoints, tests, and acceptance criteria.

The project goal is not only to produce working code, but also to produce readable educational source code. Students should be able to learn the Band (2003) sensitivity formulation and the numerical implementation by reading the source files.

---

## 1. Global Rules for Codex

### 1.1 Read the design specification first

Before editing files, read:

```text
grb_sensitivity_design_spec.md
```

Do not implement behavior that contradicts the design specification.

If the design specification and this implementation instruction conflict, stop and report the conflict instead of guessing.

### 1.2 Keep the code educational

Core physics functions must include comments that explain:

- What physical quantity is being computed.
- Which variables correspond to Band (2003) notation.
- What units are used.
- What approximation is being made.
- Why the numerical integration is performed in the chosen way.

Avoid overly compact code in the core calculation. Clarity is preferred over cleverness.

### 1.3 Preserve Band (2003)-like variable names in core functions

Use local variable names close to the paper notation where appropriate:

```text
E_l, E_h
E_1, E_2
E_p, E_0, E_b
N_E, N_T_E
A, f_det, f_mask
eta_E
Omega
N_B_E, B_E
R_int_cps
sigma_0
F_T
Delta_t
```

Public APIs and YAML fields may use more descriptive names such as `epeak_keV`, `epivot_keV`, and `accumulation_time_s`.

### 1.4 Do not silently change scientific assumptions

Do not silently:

- Change the reference flux band from 1-1000 keV.
- Change the trigger statistic from Gaussian `S/sqrt(B)`.
- Include mask open fraction inside the response unless explicitly configured.
- Accept zero response values in log-log interpolation.
- Replace the Moretti et al. (2009) CXB model with another model.

If a change is scientifically necessary, document it and ask for review.

### 1.5 Always run tests before reporting completion

At the end of each stage, run all tests available at that stage.

Do not proceed to the next stage until all tests for the current stage pass.

---

## 2. Required Human Review Checkpoints

Some checks require human inspection because they are about scientific interpretation, consistency with papers, and educational readability. These are intentionally included as project gates.

Codex must produce review artifacts at the end of each stage and explicitly list what the human user should check.

### 2.1 Human Review A: Project skeleton and CLI behavior

After Stage 1, the human user should check:

- The command names are understandable.
- The generated default YAML is readable.
- The interactive questions are understandable to students.
- The user-facing and developer-facing help text are useful and not too terse.

### 2.2 Human Review B: Equation-to-code correspondence

After Stage 2, the human user should check:

- The Band function implementation matches the intended formula.
- `E_0`, `E_b`, and `Epeak` are defined consistently.
- The threshold flux calculation corresponds to the Band (2003) formulation.
- The code comments help connect the paper equation to the implementation.
- The Moretti et al. (2009) CXB formula, per-steradian convention, and
  sr^-1 to deg^-2 reporting/check conversion are visibly correct.

Codex should provide a short markdown note:

```text
review_notes_stage2_equations.md
```

This note should list the key equations and point to the source files and functions where they are implemented.

### 2.3 Human Review C: Numerical sanity checks

After Stage 3, the human user should check:

- The sensitivity curve shape is physically plausible.
- The threshold flux is not obviously off by orders of magnitude.
- Warnings appear when the response CSV or CXB model is extrapolated.
- A simple hand-check case gives an understandable result.

Codex should provide a small output bundle from examples:

```text
examples/output/example_curve.csv
examples/output/example_curve.png
examples/output/example_significance.csv
```

### 2.4 Human Review D: Final educational readability

After Stage 4, the human user should check:

- README is sufficient for students.
- `--user-help` is enough for normal use.
- `--developer-help` is enough for reading and modifying the code.
- Core files are commented enough for learning.
- Validation errors are written in clear English.

---

## 3. Stage 1 — Project Skeleton, Configuration, and Mock CLI

### 3.1 Goal

Create the package skeleton, command-line interface, configuration loading, commented YAML template generation, and mock run behavior.

At this stage, the physical calculation may be a placeholder, but the CLI structure must be realistic.

### 3.2 Files to create

Create the following package layout:

```text
grb_sensitivity/
  __init__.py
  cli.py
  config_schema.py
  config_io.py
  wizard.py
  help_text.py
  spectra.py
  response.py
  background.py
  detector.py
  sensitivity.py
  output.py

examples/
  detector_response_efficiency.csv
  detector_response_effective_area.csv
  example_curve.yaml
  example_significance.yaml

tests/
  test_config_validation.py
  test_cli_basic.py
```

If using a package manager layout, also create:

```text
pyproject.toml
README.md
```

### 3.3 CLI commands to implement in Stage 1

Implement these commands:

```bash
grb-sens --help
grb-sens --user-help
grb-sens --developer-help
grb-sens help user
grb-sens help developer
grb-sens init
grb-sens template
grb-sens validate --config grb_sensitivity.yaml
grb-sens run --config grb_sensitivity.yaml --dry-run
```

The command:

```bash
grb-sens run --config grb_sensitivity.yaml --dry-run
```

shall load the YAML, validate it, and print a summary. It does not need to compute the real sensitivity yet.

### 3.4 Interactive behavior

If the user runs:

```bash
grb-sens
```

and no `grb_sensitivity.yaml` exists in the current directory, prompt:

```text
No configuration file was found in the current directory.
Would you like to create a new grb_sensitivity.yaml interactively? [Y/n]
```

If `grb_sensitivity.yaml` exists, prompt:

```text
Found configuration file: grb_sensitivity.yaml
Use this configuration and run the calculation? [Y/n]
```

If the user declines and asks to create a new configuration, rename the old one:

```text
grb_sensitivity_YYYYMMDD_HHMMSS.yaml.bak
```

Do not overwrite existing configuration files silently.

### 3.5 YAML wizard requirements

The wizard must ask for `response.quantity` with no default:

```text
Select detector response quantity:
  1) efficiency          - CSV value is dimensionless detection efficiency
  2) effective_area_cm2  - CSV value already includes collecting area
Enter choice [1/2]:
```

Most other fields should have defaults and accept Enter.

Use the defaults specified in `grb_sensitivity_design_spec.md`.

### 3.6 Stage 1 tests

Implement tests for:

- `--help` exits successfully.
- `--user-help` exits successfully and contains "Quick start".
- `--developer-help` exits successfully and contains "Band (2003)".
- `template` prints or writes a YAML-like template.
- `validate` accepts `examples/example_curve.yaml`.
- `validate` rejects a config with missing `response.quantity`.
- `run --dry-run` prints a readable summary.

### 3.7 Stage 1 human review artifact

Create:

```text
review_notes_stage1_cli.md
```

It shall contain:

- A list of implemented commands.
- Example terminal outputs.
- A short explanation of the interactive YAML creation flow.
- Items the human user should inspect manually.

### 3.8 Stage 1 acceptance criteria

Stage 1 is complete when:

```bash
pytest
grb-sens --help
grb-sens --user-help
grb-sens --developer-help
grb-sens validate --config examples/example_curve.yaml
grb-sens run --config examples/example_curve.yaml --dry-run
```

all work.

Stop after Stage 1 and report the status.

---

## 4. Stage 2 — Core Physics and Numerical Calculation

### 4.1 Goal

Implement the core physics and numerical calculations with unit tests.

The command-line interface may still be simple, but the Python API must compute correct values.

### 4.2 Implement Band spectrum

In `spectra.py`, implement a Band spectrum class or function set.

Required capabilities:

- Compute `E_0` from `E_p`.
- Compute `E_b`.
- Evaluate `N(E) = dN/dE`.
- Integrate photon flux over an energy band.
- Integrate energy flux over an energy band.
- Renormalize the spectrum by photon flux over a specified band.

Use educational comments.

Validation rules:

```text
alpha > -2
alpha > beta
Epeak > 0
Epivot > 0
```

### 4.3 Implement detector response

In `response.py`, implement:

- CSV loading.
- Column selection by name or 1-based column number.
- Positive-value validation.
- Log-log interpolation.
- Power-law extrapolation with warning.

Do not accept zero or negative response values.

### 4.4 Implement Moretti et al. (2009) CXB model

In `background.py`, implement built-in model:

```text
model: moretti2009
```

Use Eq. (4) 2SJPL:

```text
dN/dE = C / [ (E/E_B)^Gamma1 + (E/E_B)^Gamma2 ]
```

with:

```text
C = 0.109
Gamma1 = 1.40
Gamma2 = 2.88
E_B = 29.0 keV
```

Treat `C = 0.109` as a per-steradian normalization. The built-in
`moretti2009` model shall return photon intensity in:

```text
ph cm^-2 s^-1 sr^-1 keV^-1
```

Do not multiply the model by `(180/pi)^2` for internal detector background
calculations. For reporting or checking flux per square degree, convert from
per steradian to per square degree by dividing by:

```text
DEG2_PER_SR = (180/pi)^2
```

Implement policies:

```text
below_valid_range_policy: truncate_with_warning
above_valid_range_policy: evaluate_with_warning
```

### 4.5 Implement detector and background counts

In `detector.py` and `sensitivity.py`, implement:

```text
A_eff_pre_mask(E)
source_counts
background_counts_cxb
background_counts_internal
background_counts_total
significance_sigma
```

Use the conventions in the design specification.

If total background counts are zero or negative, raise a clear error.

### 4.6 Implement threshold flux

Implement the Band (2003)-style threshold peak photon flux calculation.

For each `Epeak`, compute the normalization needed to satisfy:

```text
source_counts / sqrt(background_counts_total) = sigma_0
```

Then compute:

```text
F_T = integral_{E_l}^{E_h} N_T(E) dE
```

Default:

```text
E_l = 1 keV
E_h = 1000 keV
sigma_0 = 8.0
```

### 4.7 Stage 2 unit tests

Add tests:

```text
tests/test_band_spectrum.py
tests/test_response.py
tests/test_background_moretti2009.py
tests/test_sensitivity.py
```

Required tests:

1. Band spectrum returns positive values for valid parameters.
2. Band spectrum rejects invalid `alpha`, `beta`, or `Epeak`.
3. Photon flux integration scales linearly with `N0`.
4. Energy flux integration uses the correct keV-to-erg conversion.
5. Response interpolation reproduces tabulated points.
6. Response interpolation rejects zero and negative values.
7. Moretti 2009 2-10 keV energy flux is close to the reported per-square-degree value after integrating `E * N_B(E)`, multiplying by `KEV_TO_ERG`, and dividing by `DEG2_PER_SR = (180/pi)^2`:
   ```text
   2.21e-11 erg cm^-2 s^-1 deg^-2
   ```
8. Moretti model uses sr^-1 internally and converts sr^-1 to deg^-2 correctly for reporting/checks.
9. Internal background counts equal `R_int_cps * Delta_t`.
10. Threshold flux decreases when detector area is increased, all else equal.
11. Significance increases when input GRB peak flux is increased.

### 4.8 Stage 2 human review artifact

Create:

```text
review_notes_stage2_equations.md
```

It shall include:

- Band function equation and source-code location.
- `E_0` and `E_b` definitions and source-code location.
- Threshold flux equation and source-code location.
- Moretti 2009 CXB equation, per-steradian convention, reporting/check conversion, and source-code location.
- Unit conversion notes.
- A checklist for the human user to visually compare the code with the papers.

### 4.9 Stage 2 acceptance criteria

Stage 2 is complete when:

```bash
pytest tests/test_band_spectrum.py tests/test_response.py tests/test_background_moretti2009.py tests/test_sensitivity.py
```

passes, and `review_notes_stage2_equations.md` is created.

Stop after Stage 2 and report the status.

---

## 5. Stage 3 — Full CLI Run, Interactive YAML, and Example Outputs

### 5.1 Goal

Connect the core physics engine to the CLI. The tool shall run real calculations from YAML files.

### 5.2 Implement `run`

Implement:

```bash
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

For `curve` mode:

- Generate a sensitivity curve over the configured Epeak grid.
- Write the configured output CSV.
- Write the configured plot if `output.plot` is set.

For `significance` mode:

- Compute source counts.
- Compute background counts.
- Compute significance.
- Write the configured output CSV.

### 5.3 Output files

Curve mode CSV columns:

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

Significance mode CSV columns:

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

### 5.4 Plot

For curve mode, produce a PNG plot.

Default axes:

```text
x-axis: Epeak [keV]
y-axis: threshold photon flux [ph cm^-2 s^-1]
```

Use logarithmic axes by default.

### 5.5 Interactive CLI tests

Add tests for wizard behavior:

- No config found: prompts to create config.
- Existing config found: prompts to use it.
- Existing config declined and new config created: old config is timestamp-backed up.
- `response.quantity` cannot be empty.
- Invalid selection for `response.quantity` causes re-prompting.
- Generated YAML validates successfully.

The tests may use monkeypatching of `input()` or subprocess interaction.

### 5.6 Stage 3 human review artifact

Create example outputs:

```text
examples/output/example_curve.csv
examples/output/example_curve.png
examples/output/example_significance.csv
```

Create:

```text
review_notes_stage3_outputs.md
```

It shall include:

- How the example outputs were generated.
- A short explanation of expected qualitative behavior.
- Warnings emitted during the run.
- Human checklist for numerical sanity inspection.

### 5.7 Stage 3 acceptance criteria

Stage 3 is complete when:

```bash
pytest
grb-sens run --config examples/example_curve.yaml
grb-sens run --config examples/example_significance.yaml
```

both work and produce output files.

Stop after Stage 3 and report the status.

---

## 6. Stage 4 — Documentation, Help Text, Robustness, and Final Polish

### 6.1 Goal

Make the tool usable by students and maintainable by future developers.

### 6.2 User documentation

Update `README.md` with:

- What the tool does.
- Installation instructions.
- Quick start.
- How to create YAML interactively.
- How to run curve mode.
- How to run significance mode.
- CSV response format.
- Explanation of important YAML fields.
- Common warnings.
- Example outputs.

### 6.3 CLI help text

Ensure these work:

```bash
grb-sens --user-help
grb-sens --developer-help
grb-sens help user
grb-sens help developer
```

`--user-help` shall be a user manual.

`--developer-help` shall be a developer and educational guide.

### 6.4 Robust validation and error messages

Improve validation messages so that students can understand how to fix input mistakes.

Examples:

```text
response.quantity is required. Choose either 'efficiency' or 'effective_area_cm2'.
```

```text
The response CSV contains zero or negative values, but log-log interpolation requires positive values.
```

```text
The Moretti 2009 CXB model is being evaluated above 200 keV. This is an extrapolation.
```

### 6.5 Final test suite

Ensure all tests pass:

```bash
pytest
```

Add any missing tests for:

- CLI help text.
- YAML template generation.
- Output CSV columns.
- Plot file creation.
- Warning messages.

### 6.6 Final human review artifact

Create:

```text
review_notes_stage4_final.md
```

It shall include:

- Final command examples.
- List of implemented features.
- List of intentionally out-of-scope items.
- Human educational readability checklist.
- Known limitations.

### 6.7 Stage 4 acceptance criteria

Stage 4 is complete when:

1. `pytest` passes.
2. README is updated.
3. `--user-help` and `--developer-help` are informative.
4. Example YAML files run successfully.
5. Example output files are generated.
6. Review notes for all stages exist.
7. The code contains educational comments in core physics modules.

---

## 7. Final Report Format

When reporting final completion, Codex should provide:

```text
Implemented stages:
- Stage 1: ...
- Stage 2: ...
- Stage 3: ...
- Stage 4: ...

Commands tested:
- ...

Files changed:
- ...

Output examples:
- ...

Known limitations:
- ...

Human review recommended:
- ...
```

Do not claim scientific validation beyond the implemented tests and human-reviewed checks.

---

## 8. Important Scientific Cautions to Preserve in Documentation

The documentation must clearly state:

1. v0.1 uses the Gaussian approximation `S/sqrt(B)`.
2. v0.1 does not model full detector response matrices.
3. v0.1 does not model particle background except as a user-supplied trigger-band count rate.
4. The Moretti 2009 CXB model is primarily intended for the X-ray/hard-X-ray band.
5. Use above 200 keV is allowed but shall be warned as extrapolation.
6. The default internal background of 0 counts/s is a mathematical default, not a realistic detector background.
7. A real instrument sensitivity study should use measured or simulated internal background.
8. LAT-LLE-related bands may be included as report bands, but a full LAT-LLE sensitivity calculation is out of scope for v0.1.
