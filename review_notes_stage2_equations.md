# Stage 2 Equation Review Notes

## Band Spectrum

- Equation: `N(E) = dN/dE` with the standard low-energy exponential branch and high-energy power-law branch.
- Source: `grb_sensitivity/spectra.py`, `BandSpectrum.evaluate`.
- Key definitions:
  - `E_0 = E_p / (alpha + 2)` in `BandSpectrum.e0_keV`.
  - `E_b = (alpha - beta) * E_0` in `BandSpectrum.ebreak_keV`.
- Unit convention: `N(E)` returns `ph cm^-2 s^-1 keV^-1`; energy flux multiplies by `KEV_TO_ERG`.

## Detector Response

- Equation: response is interpolated linearly in `log(E)` and `log(value)`.
- Source: `grb_sensitivity/response.py`, `DetectorResponse.evaluate`.
- Positive energy and response values are required because log-log interpolation cannot represent zero or negative values.

## Counts And Significance

- Source counts:
  `source_counts = Delta_t * f_mask * integral A_eff_pre_mask(E) * N(E) dE`
- CXB counts:
  `cxb_counts = Delta_t * f_mask * Omega * integral A_eff_pre_mask(E) * N_B(E) dE`
- Internal background:
  `background_counts_internal = R_int_cps * Delta_t`
- Significance:
  `significance_sigma = source_counts / sqrt(background_counts_total)`
- Source: `grb_sensitivity/sensitivity.py`.

## Threshold Flux

- For a trial spectrum with `N0 = 1`, Stage 2 computes `source_counts_per_N0`.
- The threshold scale is:
  `scale_to_threshold = sigma_0 * sqrt(background_counts_total) / source_counts_per_N0`
- The reported threshold photon flux is:
  `F_T = integral_{E_l}^{E_h} N_T(E) dE`
- Source: `grb_sensitivity/sensitivity.py`, `threshold_peak_photon_flux`.

## Moretti 2009 CXB

- Equation:
  `dN/dE = C / [(E/E_B)^Gamma1 + (E/E_B)^Gamma2]`
- Parameters:
  `C = 0.109`, `Gamma1 = 1.40`, `Gamma2 = 2.88`, `E_B = 29.0 keV`.
- Corrected unit convention: `C = 0.109` is treated as per steradian.
- Built-in model output: `ph cm^-2 s^-1 sr^-1 keV^-1`.
- Detector background uses the sr^-1 model directly and multiplies by `Omega` in sr.
- Per-square-degree checks divide by `DEG2_PER_SR = (180/pi)^2`.
- Source: `grb_sensitivity/background.py`.

## Human Checklist

- Compare the Band low/high branch normalization against the intended Band function.
- Confirm `E_0`, `E_b`, and `Epeak` definitions match the design spec.
- Check that mask factors are applied outside `A_eff_pre_mask(E)`.
- Confirm Moretti 2009 is not multiplied by `(180/pi)^2` internally.
- Confirm the 2-10 keV check reports per square degree only after dividing by `DEG2_PER_SR`.
