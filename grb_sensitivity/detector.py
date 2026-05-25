"""Detector geometry and pre-mask effective-area convention."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .response import DetectorResponse


@dataclass(frozen=True)
class Detector:
    """Detector model used by the v0.1 count equations.

    The core calculation uses ``A_eff_pre_mask(E)``. Coded-mask open fraction is
    applied later to source and CXB counts, so it is not silently folded into the
    response unless ``response_includes_mask`` says the response already has it.
    """

    response: DetectorResponse
    geometric_area_cm2: float = 100.0
    active_fraction: float = 1.0
    aperture_solid_angle_sr: float = 1.0
    mask_open_fraction: float = 1.0
    response_includes_mask: bool = False

    def __post_init__(self) -> None:
        if self.geometric_area_cm2 <= 0:
            raise ValueError("geometric_area_cm2 must be positive.")
        if not (0 < self.active_fraction <= 1):
            raise ValueError("active_fraction must be greater than 0 and no larger than 1.")
        if self.aperture_solid_angle_sr <= 0:
            raise ValueError("aperture_solid_angle_sr must be positive.")
        if not (0 < self.mask_open_fraction <= 1):
            raise ValueError("mask_open_fraction must be greater than 0 and no larger than 1.")

    def effective_area_pre_mask(self, E_keV):
        """Return ``A_eff_pre_mask(E)`` in cm^2.

        For an efficiency response, ``A_eff_pre_mask(E) = A * f_det * eta(E)``.
        For an effective-area response, the CSV value is already the collecting
        area before the coded-mask factor, following the design specification.
        """

        if self.response.quantity == "efficiency":
            A = self.geometric_area_cm2
            f_det = self.active_fraction
            eta_E = self.response(E_keV)
            A_eff_pre_mask = A * f_det * eta_E
        else:
            A_eff_pre_mask = self.response(E_keV)
        return A_eff_pre_mask

    def mask_factor(self, *, applies: bool) -> float:
        """Return the mask factor used for source or CXB counts."""

        if not applies:
            return 1.0
        if self.response_includes_mask:
            # Avoid double-counting the coded mask when a response curve already
            # includes it. The YAML should make this convention explicit.
            return 1.0
        f_mask = self.mask_open_fraction
        return float(f_mask)


def make_flat_efficiency_detector(
    *,
    geometric_area_cm2: float = 100.0,
    efficiency: float = 1.0,
    active_fraction: float = 1.0,
    aperture_solid_angle_sr: float = 1.0,
    mask_open_fraction: float = 1.0,
) -> Detector:
    """Construct a simple detector useful for tests and hand checks."""

    response = DetectorResponse(
        energy_keV=np.array([1.0, 1.0e5]),
        values=np.array([efficiency, efficiency]),
        quantity="efficiency",
    )
    return Detector(
        response=response,
        geometric_area_cm2=geometric_area_cm2,
        active_fraction=active_fraction,
        aperture_solid_angle_sr=aperture_solid_angle_sr,
        mask_open_fraction=mask_open_fraction,
    )
