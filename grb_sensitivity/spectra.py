"""Band GRB photon spectrum and numerical integrations.

The Band model is written here in a deliberately direct style so students can
match the code to the equations in the design document. Energies are keV and
the photon spectrum ``N(E)`` has units ``ph cm^-2 s^-1 keV^-1``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

KEV_TO_ERG = 1.602176634e-9


def _trapz(y, x) -> float:
    """Use NumPy's trapezoid rule, with a compatibility fallback.

    v0.1 intentionally uses a log-spaced energy grid and trapezoidal
    integration instead of scipy quadrature so the numerical method is visible.
    """

    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def log_energy_grid(E_min_keV: float, E_max_keV: float, n_grid: int = 4096) -> np.ndarray:
    """Return a log-spaced grid for positive photon energies in keV."""

    if E_min_keV <= 0 or E_max_keV <= E_min_keV:
        raise ValueError("Energy integration bounds must satisfy 0 < E_min < E_max.")
    if n_grid < 2:
        raise ValueError("Integration grid must contain at least two points.")
    return np.logspace(np.log10(E_min_keV), np.log10(E_max_keV), int(n_grid))


def integrate_log_grid(
    function: Callable[[np.ndarray], np.ndarray],
    E_min_keV: float,
    E_max_keV: float,
    n_grid: int = 4096,
) -> float:
    """Integrate ``function(E)`` over energy in keV on a log-spaced grid."""

    E_grid = log_energy_grid(E_min_keV, E_max_keV, n_grid)
    y_grid = function(E_grid)
    return _trapz(y_grid, E_grid)


@dataclass(frozen=True)
class BandSpectrum:
    """Band photon spectrum ``N(E) = dN/dE``.

    ``N0`` is the normalization at ``epivot_keV`` in
    ``ph cm^-2 s^-1 keV^-1``. ``epeak_keV`` is the peak energy of ``E^2 N(E)``.
    """

    alpha: float = -1.0
    beta: float = -2.5
    epeak_keV: float = 500.0
    epivot_keV: float = 100.0
    N0: float = 1.0

    def __post_init__(self) -> None:
        if self.alpha <= -2.0:
            raise ValueError("alpha must be greater than -2 so E_0 = Epeak / (alpha + 2) is positive.")
        if self.alpha <= self.beta:
            raise ValueError("alpha must be greater than beta for a valid Band spectrum.")
        if self.epeak_keV <= 0:
            raise ValueError("epeak_keV must be positive.")
        if self.epivot_keV <= 0:
            raise ValueError("epivot_keV must be positive.")
        if self.N0 <= 0:
            raise ValueError("N0 must be positive.")

    @property
    def e0_keV(self) -> float:
        """Band e-folding energy ``E_0 = E_p / (alpha + 2)`` in keV."""

        E_p = self.epeak_keV
        E_0 = E_p / (self.alpha + 2.0)
        return E_0

    @property
    def ebreak_keV(self) -> float:
        """Band break energy ``E_b = (alpha - beta) E_0`` in keV."""

        E_0 = self.e0_keV
        E_b = (self.alpha - self.beta) * E_0
        return E_b

    def evaluate(self, E_keV):
        """Evaluate ``N(E)`` in ``ph cm^-2 s^-1 keV^-1``.

        Below ``E_b`` the Band function is a power law with an exponential
        cutoff. Above ``E_b`` it is a pure power law with the normalization
        chosen so the two branches meet continuously.
        """

        E = np.asarray(E_keV, dtype=float)
        if np.any(E <= 0):
            raise ValueError("Photon energies must be positive.")

        N0 = self.N0
        alpha = self.alpha
        beta = self.beta
        E_pivot = self.epivot_keV
        E_0 = self.e0_keV
        E_b = self.ebreak_keV

        low_branch = N0 * (E / E_pivot) ** alpha * np.exp(-E / E_0)
        high_prefactor = ((alpha - beta) * E_0 / E_pivot) ** (alpha - beta) * np.exp(beta - alpha)
        high_branch = N0 * high_prefactor * (E / E_pivot) ** beta
        N_E = np.where(E <= E_b, low_branch, high_branch)

        if np.isscalar(E_keV):
            return float(N_E)
        return N_E

    __call__ = evaluate

    def photon_flux(self, band_keV: tuple[float, float] | list[float], n_grid: int = 4096) -> float:
        """Integrate photon flux ``integral N(E) dE`` over an energy band."""

        E_l, E_h = float(band_keV[0]), float(band_keV[1])
        return integrate_log_grid(self.evaluate, E_l, E_h, n_grid)

    def energy_flux(self, band_keV: tuple[float, float] | list[float], n_grid: int = 4096) -> float:
        """Integrate energy flux in ``erg cm^-2 s^-1`` over an energy band."""

        E_l, E_h = float(band_keV[0]), float(band_keV[1])

        def E_N_E(E_grid: np.ndarray) -> np.ndarray:
            # E * N(E) gives keV cm^-2 s^-1 keV^-1 before multiplying by dE.
            return E_grid * self.evaluate(E_grid) * KEV_TO_ERG

        return integrate_log_grid(E_N_E, E_l, E_h, n_grid)

    def renormalized_to_photon_flux(
        self,
        target_flux_ph_cm2_s: float,
        band_keV: tuple[float, float] | list[float],
        n_grid: int = 4096,
    ) -> "BandSpectrum":
        """Return a copy whose photon flux over ``band_keV`` equals target.

        The Band function is linear in ``N0``, so renormalization is a simple
        scale factor based on the current integrated photon flux.
        """

        if target_flux_ph_cm2_s <= 0:
            raise ValueError("target photon flux must be positive.")
        current_flux = self.photon_flux(band_keV, n_grid)
        if current_flux <= 0:
            raise ValueError("current photon flux is not positive; cannot renormalize.")
        scale = target_flux_ph_cm2_s / current_flux
        return BandSpectrum(
            alpha=self.alpha,
            beta=self.beta,
            epeak_keV=self.epeak_keV,
            epivot_keV=self.epivot_keV,
            N0=self.N0 * scale,
        )
