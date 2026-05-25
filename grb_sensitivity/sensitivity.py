"""Band (2003)-style source counts, background counts, and threshold flux."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .background import cxb_effective_band, internal_background_counts, moretti2009_photon_intensity
from .detector import Detector
from .spectra import BandSpectrum, integrate_log_grid


@dataclass(frozen=True)
class BackgroundCounts:
    cxb: float
    internal: float

    @property
    def total(self) -> float:
        return self.cxb + self.internal


@dataclass(frozen=True)
class ThresholdResult:
    epeak_keV: float
    threshold_photon_flux_ph_cm2_s: float
    threshold_energy_flux_erg_cm2_s: float
    source_counts_at_threshold: float
    background_counts_total: float
    background_counts_cxb: float
    background_counts_internal: float
    source_counts_per_N0: float
    scale_to_threshold: float


def source_counts(
    spectrum: BandSpectrum,
    detector: Detector,
    trigger_band_keV: tuple[float, float] | list[float],
    Delta_t: float,
    *,
    n_grid: int = 4096,
    apply_mask: bool = True,
) -> float:
    """Compute source counts in the detector trigger band ``[E_1, E_2]``.

    This is the v0.1 direct count equation:
    ``Delta_t * f_mask * integral A_eff_pre_mask(E) * N(E) dE``.
    ``N(E)`` is photon flux density and ``A_eff_pre_mask`` is cm^2, so the
    integral is counts/s before multiplying by accumulation time.
    """

    E_1, E_2 = float(trigger_band_keV[0]), float(trigger_band_keV[1])
    if Delta_t <= 0:
        raise ValueError("Delta_t must be positive.")
    f_mask = detector.mask_factor(applies=apply_mask)

    def source_rate_integrand(E_grid: np.ndarray) -> np.ndarray:
        A_eff_pre_mask = detector.effective_area_pre_mask(E_grid)
        N_E = spectrum.evaluate(E_grid)
        return A_eff_pre_mask * N_E

    source_rate_cps = integrate_log_grid(source_rate_integrand, E_1, E_2, n_grid)
    return float(Delta_t) * f_mask * source_rate_cps


def background_counts_cxb(
    detector: Detector,
    trigger_band_keV: tuple[float, float] | list[float],
    Delta_t: float,
    *,
    enabled: bool = True,
    model: str = "moretti2009",
    below_valid_range_policy: str = "truncate_with_warning",
    above_valid_range_policy: str = "evaluate_with_warning",
    n_grid: int = 4096,
    apply_mask: bool = True,
) -> float:
    """Compute sky CXB background counts.

    The Moretti 2009 model returns ``N_B(E)`` per steradian. The count equation
    multiplies by aperture solid angle ``Omega`` in steradians:
    ``Delta_t * f_mask * Omega * integral A_eff_pre_mask(E) * N_B(E) dE``.
    """

    if not enabled:
        return 0.0
    if model != "moretti2009":
        raise ValueError("Only the built-in 'moretti2009' CXB model is implemented in v0.1.")
    if Delta_t <= 0:
        raise ValueError("Delta_t must be positive.")

    E_1, E_2 = float(trigger_band_keV[0]), float(trigger_band_keV[1])
    E_cxb_low, E_cxb_high = cxb_effective_band(
        E_1,
        E_2,
        below_valid_range_policy=below_valid_range_policy,
        above_valid_range_policy=above_valid_range_policy,
    )
    f_mask = detector.mask_factor(applies=apply_mask)
    Omega = detector.aperture_solid_angle_sr

    def cxb_rate_integrand(E_grid: np.ndarray) -> np.ndarray:
        A_eff_pre_mask = detector.effective_area_pre_mask(E_grid)
        N_B_E = moretti2009_photon_intensity(E_grid)
        return A_eff_pre_mask * N_B_E

    cxb_rate_cps = integrate_log_grid(cxb_rate_integrand, E_cxb_low, E_cxb_high, n_grid)
    return float(Delta_t) * f_mask * Omega * cxb_rate_cps


def background_counts_total(
    detector: Detector,
    trigger_band_keV: tuple[float, float] | list[float],
    Delta_t: float,
    *,
    R_int_cps: float = 0.0,
    cxb_enabled: bool = True,
    cxb_model: str = "moretti2009",
    below_valid_range_policy: str = "truncate_with_warning",
    above_valid_range_policy: str = "evaluate_with_warning",
    n_grid: int = 4096,
) -> BackgroundCounts:
    """Return CXB, internal, and total background counts."""

    cxb_counts = background_counts_cxb(
        detector,
        trigger_band_keV,
        Delta_t,
        enabled=cxb_enabled,
        model=cxb_model,
        below_valid_range_policy=below_valid_range_policy,
        above_valid_range_policy=above_valid_range_policy,
        n_grid=n_grid,
        apply_mask=True,
    )
    internal_counts = internal_background_counts(R_int_cps, Delta_t)
    return BackgroundCounts(cxb=cxb_counts, internal=internal_counts)


def significance_sigma(source_counts_value: float, background_counts_value: float) -> float:
    """Gaussian trigger significance ``S / sqrt(B)``."""

    if background_counts_value <= 0:
        raise ValueError("background_counts_total must be positive for Gaussian S/sqrt(B) significance.")
    return float(source_counts_value) / math.sqrt(float(background_counts_value))


def threshold_peak_photon_flux(
    *,
    alpha: float,
    beta: float,
    epeak_keV: float,
    epivot_keV: float,
    detector: Detector,
    trigger_band_keV: tuple[float, float] | list[float],
    reference_band_keV: tuple[float, float] | list[float] = (1.0, 1000.0),
    Delta_t: float = 1.0,
    sigma_0: float = 8.0,
    R_int_cps: float = 0.0,
    cxb_enabled: bool = True,
    cxb_model: str = "moretti2009",
    below_valid_range_policy: str = "truncate_with_warning",
    above_valid_range_policy: str = "evaluate_with_warning",
    precomputed_background: BackgroundCounts | None = None,
    n_grid: int = 4096,
) -> ThresholdResult:
    """Compute Band (2003)-style threshold peak photon flux ``F_T``.

    A trial Band spectrum with ``N0 = 1`` is used to compute
    ``source_counts_per_N0``. Since counts are linear in ``N0``, the threshold
    normalization is ``sigma_0 * sqrt(background_counts_total) /
    source_counts_per_N0``. The threshold photon flux ``F_T`` is then the
    reference-band photon flux of the scaled threshold spectrum ``N_T(E)``.
    """

    if sigma_0 <= 0:
        raise ValueError("sigma_0 must be positive.")

    E_l, E_h = float(reference_band_keV[0]), float(reference_band_keV[1])
    E_1, E_2 = float(trigger_band_keV[0]), float(trigger_band_keV[1])
    E_p = float(epeak_keV)

    trial_spectrum = BandSpectrum(alpha=alpha, beta=beta, epeak_keV=E_p, epivot_keV=epivot_keV, N0=1.0)
    # Expose the Band notation in code so the relation to the paper is visible.
    E_0 = trial_spectrum.e0_keV
    E_b = trial_spectrum.ebreak_keV
    _ = (E_0, E_b)

    source_counts_per_N0 = source_counts(trial_spectrum, detector, (E_1, E_2), Delta_t, n_grid=n_grid)
    if source_counts_per_N0 <= 0:
        raise ValueError("source_counts_per_N0 must be positive to compute a threshold flux.")

    if precomputed_background is None:
        background = background_counts_total(
            detector,
            (E_1, E_2),
            Delta_t,
            R_int_cps=R_int_cps,
            cxb_enabled=cxb_enabled,
            cxb_model=cxb_model,
            below_valid_range_policy=below_valid_range_policy,
            above_valid_range_policy=above_valid_range_policy,
            n_grid=n_grid,
        )
    else:
        background = precomputed_background
    background_counts_total_value = background.total
    if background_counts_total_value <= 0:
        raise ValueError("background_counts_total must be positive to compute a threshold flux.")

    scale_to_threshold = sigma_0 * math.sqrt(background_counts_total_value) / source_counts_per_N0
    threshold_spectrum = BandSpectrum(
        alpha=alpha,
        beta=beta,
        epeak_keV=E_p,
        epivot_keV=epivot_keV,
        N0=scale_to_threshold,
    )
    N_T_E = threshold_spectrum
    F_T = N_T_E.photon_flux((E_l, E_h), n_grid)
    threshold_energy_flux = N_T_E.energy_flux((E_l, E_h), n_grid)
    source_counts_at_threshold = source_counts_per_N0 * scale_to_threshold

    return ThresholdResult(
        epeak_keV=E_p,
        threshold_photon_flux_ph_cm2_s=F_T,
        threshold_energy_flux_erg_cm2_s=threshold_energy_flux,
        source_counts_at_threshold=source_counts_at_threshold,
        background_counts_total=background_counts_total_value,
        background_counts_cxb=background.cxb,
        background_counts_internal=background.internal,
        source_counts_per_N0=source_counts_per_N0,
        scale_to_threshold=scale_to_threshold,
    )


def significance_for_peak_flux(
    *,
    alpha: float,
    beta: float,
    epeak_keV: float,
    epivot_keV: float,
    peak_flux_ph_cm2_s: float,
    peak_flux_band_keV: tuple[float, float] | list[float],
    detector: Detector,
    trigger_band_keV: tuple[float, float] | list[float],
    Delta_t: float = 1.0,
    R_int_cps: float = 0.0,
    cxb_enabled: bool = True,
    cxb_model: str = "moretti2009",
    below_valid_range_policy: str = "truncate_with_warning",
    above_valid_range_policy: str = "evaluate_with_warning",
    n_grid: int = 4096,
) -> float:
    """Compute Gaussian significance for a GRB with known peak photon flux."""

    spectrum = BandSpectrum(alpha=alpha, beta=beta, epeak_keV=epeak_keV, epivot_keV=epivot_keV, N0=1.0)
    normalized = spectrum.renormalized_to_photon_flux(peak_flux_ph_cm2_s, peak_flux_band_keV, n_grid)
    S = source_counts(normalized, detector, trigger_band_keV, Delta_t, n_grid=n_grid)
    B = background_counts_total(
        detector,
        trigger_band_keV,
        Delta_t,
        R_int_cps=R_int_cps,
        cxb_enabled=cxb_enabled,
        cxb_model=cxb_model,
        below_valid_range_policy=below_valid_range_policy,
        above_valid_range_policy=above_valid_range_policy,
        n_grid=n_grid,
    ).total
    return significance_sigma(S, B)
