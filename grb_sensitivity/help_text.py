"""Plain-text manuals printed by the CLI."""

USER_HELP = """GRB Sensitivity Calculator User Manual

Purpose
  grb-sens is an educational command-line tool for Band (2003)-style GRB
  detector sensitivity calculations. It can compute a threshold-flux curve or
  the Gaussian S/sqrt(B) significance of one configured GRB.

Quick start
  grb-sens validate --config examples/example_curve.yaml
  grb-sens run --config examples/example_curve.yaml --dry-run
  grb-sens run --config examples/example_curve.yaml
  grb-sens run --config examples/example_significance.yaml

Create a config
  Run grb-sens in a terminal with no subcommand, or run grb-sens init. If no
  grb_sensitivity.yaml exists, the wizard asks whether to create one. It will
  ask you to choose detector.response.quantity because there is no safe default:
  efficiency or effective_area_cm2.

Run curve mode
  Set mode: curve. Configure spectrum.alpha, spectrum.beta, the detector
  response CSV, detector.trigger.energy_band_keV, and curve.epeak_grid_keV.
  Then run:
    grb-sens run --config path/to/config.yaml
  The CSV contains threshold photon flux versus Epeak. If output.plot is set,
  a PNG plot is also written.

Run significance mode
  Set mode: significance. Configure grb.epeak_keV and grb.peak_flux, plus the
  same detector and background fields used by curve mode. Then run:
    grb-sens run --config path/to/config.yaml
  The CSV contains source counts, background counts, significance, and detected.

Response CSV format
  The CSV must contain positive photon energies in keV and positive response
  values. Columns may be selected by 1-based number or by column name.
  Use response.quantity: efficiency when values are dimensionless efficiency.
  Use response.quantity: effective_area_cm2 when values are collecting area in
  cm^2. Log-log interpolation requires all values to be greater than zero.

Important YAML fields
  mode: curve or significance.
  spectrum: Band alpha, beta, and epivot_keV.
  flux.reference_band_keV: photon-flux reporting band, usually [1, 1000].
  detector.response: CSV path, quantity, and columns.
  detector.trigger: trigger band [E_1, E_2], accumulation time, threshold sigma.
  background.cxb: Moretti et al. (2009) CXB model and range-warning policies.
  background.internal.rate_cps: trigger-band internal background count rate.
  output.csv and output.plot: output paths relative to the YAML file.

Common warnings
  Moretti et al. (2009) above 200 keV: the CXB model is being extrapolated above its
  nominal hard-X-ray range. This is expected for the bundled 10-1000 keV example.
  Response extrapolation: your trigger/integration range extends beyond the
  detector response CSV energy range.
  Default internal background 0 counts/s: this is a mathematical default, not a
  realistic detector model.

Example commands
  grb-sens template
  grb-sens init
  grb-sens validate --config examples/example_curve.yaml
  grb-sens run --config examples/example_curve.yaml --dry-run
  grb-sens run --config examples/example_curve.yaml
  grb-sens run --config examples/example_significance.yaml
"""


DEVELOPER_HELP = """GRB Sensitivity Calculator Developer Guide

Package layout
  grb_sensitivity.cli             command-line entry point
  grb_sensitivity.config_schema   defaults and validation rules
  grb_sensitivity.config_io       YAML loading and template generation
  grb_sensitivity.wizard          interactive configuration creation
  grb_sensitivity.spectra         Band spectrum and flux integration
  grb_sensitivity.response        response CSV loading and log-log interpolation
  grb_sensitivity.background      Moretti et al. (2009) CXB and internal background
  grb_sensitivity.detector        pre-mask effective-area and mask conventions
  grb_sensitivity.sensitivity     source/background counts, significance, F_T
  grb_sensitivity.output          CLI real-run execution, CSV, and plot output

Where equations live
  Band spectrum: spectra.py, BandSpectrum.evaluate, e0_keV, ebreak_keV.
  Detector response interpolation: response.py, DetectorResponse.evaluate.
  Moretti et al. (2009) CXB: background.py, moretti2009_photon_intensity.
  Source/background counts: sensitivity.py, source_counts and background counts.
  Threshold flux: sensitivity.py, threshold_peak_photon_flux.

Band (2003) notation to Python names
  E_l, E_h: reference photon-flux band.
  E_1, E_2: detector trigger band.
  E_p: epeak_keV.
  E_0: Band e-folding energy, e0_keV.
  E_b: Band break energy, ebreak_keV.
  N_E: photon spectrum N(E).
  A: geometric detector area.
  f_det: active detector fraction.
  f_mask: coded-mask open fraction.
  eta_E: detector efficiency.
  Omega: aperture solid angle in sr.
  N_B_E: CXB photon intensity.
  R_int_cps: trigger-band internal background rate.
  sigma_0: threshold significance.
  F_T: threshold photon flux in [E_l, E_h].
  Delta_t: accumulation time.

Unit conventions
  Energies are keV. Areas are cm^2. Photon flux is ph cm^-2 s^-1. Spectra are
  ph cm^-2 s^-1 keV^-1. Moretti et al. (2009) returns ph cm^-2 s^-1 sr^-1 keV^-1.
  Per-square-degree checks divide by DEG2_PER_SR = (180/pi)^2.

How to run tests
  pytest

Adding a background model
  Add the model in background.py, document units and validity range, expose
  clear warnings for extrapolation, and add tests for units and ranges.

Adding a spectrum model
  Add the model in spectra.py, validate parameters in config_schema.py, and add
  tests for positivity, normalization, and integration behavior.

Adding or modifying output columns
  Update output.py, README.md, and tests/test_cli_run_stage3.py so the CSV
  contract and documentation stay aligned.

Code-comment policy
  Core physics code should explain the physical quantity, units, Band (2003)
  notation, numerical approximation, and why the integration method is used.
  Prefer readable educational code over compact clever code.
"""
