"""Background models used by the sensitivity calculation."""

from __future__ import annotations

import warnings

import numpy as np

from .spectra import KEV_TO_ERG, integrate_log_grid

DEG2_PER_SR = (180.0 / np.pi) ** 2

MORETTI2009_C_PER_SR = 0.109
MORETTI2009_GAMMA1 = 1.40
MORETTI2009_GAMMA2 = 2.88
MORETTI2009_E_B_KEV = 29.0
MORETTI2009_VALID_RANGE_KEV = (10.0, 200.0)


def moretti2009_photon_intensity(E_keV):
    """Return Moretti et al. (2009) 2SJPL CXB photon intensity.

    The corrected v0.1 convention treats ``C = 0.109`` as per steradian, so the
    returned ``N_B(E)`` is in ``ph cm^-2 s^-1 sr^-1 keV^-1``. Detector
    background counts multiply this intensity by ``Omega`` in steradians
    directly; no ``(180/pi)^2`` factor is applied internally.
    """

    E = np.asarray(E_keV, dtype=float)
    if np.any(E <= 0):
        raise ValueError("CXB model energies must be positive.")
    N_B_E = MORETTI2009_C_PER_SR / (
        (E / MORETTI2009_E_B_KEV) ** MORETTI2009_GAMMA1
        + (E / MORETTI2009_E_B_KEV) ** MORETTI2009_GAMMA2
    )
    if np.isscalar(E_keV):
        return float(N_B_E)
    return N_B_E


def moretti2009_energy_flux_per_deg2(
    band_keV: tuple[float, float] | list[float] = (2.0, 10.0),
    n_grid: int = 16384,
) -> float:
    """Integrate Moretti 2009 energy flux and report per square degree.

    The model returns per-steradian photon intensity. For the published 2-10 keV
    consistency check, integrate ``E * N_B(E)`` over keV, multiply by
    ``KEV_TO_ERG``, then divide by ``DEG2_PER_SR``.
    """

    E_l, E_h = float(band_keV[0]), float(band_keV[1])

    def E_N_B_E(E_grid: np.ndarray) -> np.ndarray:
        return E_grid * moretti2009_photon_intensity(E_grid) * KEV_TO_ERG / DEG2_PER_SR

    return integrate_log_grid(E_N_B_E, E_l, E_h, n_grid)


def cxb_effective_band(
    E_1: float,
    E_2: float,
    *,
    below_valid_range_policy: str = "truncate_with_warning",
    above_valid_range_policy: str = "evaluate_with_warning",
) -> tuple[float, float]:
    """Apply v0.1 Moretti 2009 validity-range policies to a trigger band."""

    valid_low, valid_high = MORETTI2009_VALID_RANGE_KEV
    if E_1 <= 0 or E_2 <= E_1:
        raise ValueError("CXB integration bounds must satisfy 0 < E_1 < E_2.")

    E_low = E_1
    if E_1 < valid_low:
        if below_valid_range_policy != "truncate_with_warning":
            raise ValueError("Only truncate_with_warning is implemented below the Moretti 2009 valid range.")
        warnings.warn(
            "The Moretti 2009 CXB model is requested below 10 keV; the lower part of the CXB integration is truncated.",
            RuntimeWarning,
            stacklevel=2,
        )
        E_low = valid_low

    if E_2 > valid_high:
        if above_valid_range_policy != "evaluate_with_warning":
            raise ValueError("Only evaluate_with_warning is implemented above the Moretti 2009 valid range.")
        warnings.warn(
            "The Moretti 2009 CXB model is being evaluated above 200 keV. This is an extrapolation.",
            RuntimeWarning,
            stacklevel=2,
        )

    if E_low >= E_2:
        raise ValueError("CXB integration band is empty after applying the below-range truncation policy.")
    return E_low, E_2


def internal_background_counts(R_int_cps: float, Delta_t: float) -> float:
    """Return internal background counts for a trigger-band count rate.

    In Band (2003), ``B_int`` is written as a differential internal background
    term. In this v0.1 implementation, the main user-facing internal background
    input is ``R_int_cps``, the count rate already integrated over the trigger
    band ``[E_1, E_2]``.
    """

    if R_int_cps < 0:
        raise ValueError("internal background rate_cps must not be negative.")
    if Delta_t <= 0:
        raise ValueError("Delta_t must be positive.")
    return float(R_int_cps) * float(Delta_t)
