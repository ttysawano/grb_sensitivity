"""Plain-text manuals printed by the CLI."""

USER_HELP = """GRB Sensitivity Calculator

Purpose
  grb-sens is an educational command-line tool for setting up Band (2003)-style
  gamma-ray burst detector sensitivity calculations.

Quick start
  grb-sens init
  grb-sens validate --config grb_sensitivity.yaml
  grb-sens run --config grb_sensitivity.yaml --dry-run

Interactive YAML creation
  Run grb-sens with no subcommand in a terminal. If no grb_sensitivity.yaml is
  present, the program asks whether to create one interactively.

Sensitivity curve
  Use mode: curve to describe a threshold peak photon flux curve as a function
  of GRB Epeak. Stage 1 prints a dry-run summary; real physics is Stage 2+.

Known-GRB significance
  Use mode: significance with grb.epeak_keV and grb.peak_flux to describe one
  GRB spectrum. Stage 1 validates and summarizes the setup.

Required input files
  The detector response CSV is named by detector.response.path. It must contain
  energy in keV and either dimensionless efficiency or effective area in cm^2.

Response CSV format
  Columns may be selected by name or by 1-based column number. For v0.1
  log-log interpolation, energy and response values must be positive.

Major YAML fields
  mode selects curve or significance. spectrum contains Band alpha, beta, and
  pivot energy. detector.trigger contains [E_1, E_2], accumulation time, and
  threshold sigma. background.internal.rate_cps is the trigger-band internal
  background rate.

Common warnings
  A missing response CSV warning means Stage 1 did not read the response data.
  A Moretti 2009 warning above 200 keV in later stages means CXB extrapolation.

Example commands
  grb-sens template
  grb-sens validate --config examples/example_curve.yaml
  grb-sens run --config examples/example_curve.yaml --dry-run
"""


DEVELOPER_HELP = """GRB Sensitivity Calculator Developer Guide

Package layout
  grb_sensitivity.cli             command-line entry point
  grb_sensitivity.config_schema   defaults and validation rules
  grb_sensitivity.config_io       YAML loading and template generation
  grb_sensitivity.wizard          interactive configuration skeleton
  grb_sensitivity.spectra         Band spectrum implementation placeholder
  grb_sensitivity.response        detector response placeholder
  grb_sensitivity.background      CXB/background placeholder
  grb_sensitivity.detector        detector convention placeholder
  grb_sensitivity.sensitivity     Band (2003) calculation placeholder
  grb_sensitivity.output          output placeholder

Physics modules and roles
  spectra.py will evaluate the Band function N(E). response.py will load and
  interpolate eta(E) or effective area. background.py will implement the
  Moretti et al. (2009) CXB model. sensitivity.py will connect source counts,
  background counts, significance, and threshold flux.

Band (2003) notation to Python names
  E_l, E_h: reference photon-flux band.
  E_1, E_2: detector trigger band.
  Delta_t: accumulation time.
  sigma_0: threshold significance.
  F_T: threshold photon flux in [E_l, E_h].
  A, f_det, f_mask, eta_E, Omega: detector and aperture quantities.
  R_int_cps: trigger-band internal background count rate.

Unit conventions
  Energies are keV. Areas are cm^2. Photon flux is ph cm^-2 s^-1. CXB
  intensity is ph cm^-2 s^-1 sr^-1 keV^-1 after conversion from deg^-2.

Where to find the core calculation
  Stage 1 contains placeholders only. The real calculation belongs in
  spectra.py, background.py, detector.py, response.py, and sensitivity.py.

How to run tests
  pytest

Adding a background model
  Add a named model in background.py, document its units, and add validation for
  any model-specific YAML fields.

Adding a spectrum model
  Add a model in spectra.py, validate its parameters in config_schema.py, and
  keep comments close to the physical equations.

Adding an output column
  Add the value in output.py and document the units in the CSV header notes or
  README.

Code-comment policy
  Core physics code should explain the physical quantity, Band (2003) notation,
  units, numerical approximation, and why the integration method is used.
"""
