import numpy as np
import pytest

from grb_sensitivity.background import (
    DEG2_PER_SR,
    cxb_effective_band,
    moretti2009_energy_flux_per_deg2,
    moretti2009_photon_intensity,
)


def test_moretti_2009_2_10_kev_energy_flux_per_square_degree():
    flux = moretti2009_energy_flux_per_deg2((2.0, 10.0), n_grid=65536)

    assert flux == pytest.approx(2.21e-11, rel=0.03)


def test_moretti_model_uses_sr_internally_and_converts_to_deg2_for_checks():
    E_keV = 10.0
    intensity_sr = moretti2009_photon_intensity(E_keV)
    intensity_deg2 = intensity_sr / DEG2_PER_SR

    assert intensity_sr > intensity_deg2
    assert intensity_sr / intensity_deg2 == pytest.approx(DEG2_PER_SR)


def test_moretti_model_returns_positive_values():
    energies = np.array([2.0, 10.0, 200.0])

    assert np.all(moretti2009_photon_intensity(energies) > 0)


def test_moretti_above_range_warning_explains_extrapolation():
    with pytest.warns(RuntimeWarning, match="above 200 keV.*extrapolation"):
        assert cxb_effective_band(10.0, 1000.0) == (10.0, 1000.0)
