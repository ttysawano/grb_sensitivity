import numpy as np
import pytest

from grb_sensitivity.spectra import BandSpectrum, KEV_TO_ERG


def test_band_spectrum_returns_positive_values():
    spectrum = BandSpectrum(alpha=-1.0, beta=-2.5, epeak_keV=300.0)
    values = spectrum.evaluate(np.array([10.0, 100.0, 1000.0]))

    assert np.all(values > 0)
    assert spectrum.e0_keV == pytest.approx(300.0)
    assert spectrum.ebreak_keV == pytest.approx(450.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alpha": -2.0, "beta": -2.5, "epeak_keV": 300.0},
        {"alpha": -2.2, "beta": -2.5, "epeak_keV": 300.0},
        {"alpha": -2.5, "beta": -2.5, "epeak_keV": 300.0},
        {"alpha": -1.0, "beta": -2.5, "epeak_keV": 0.0},
    ],
)
def test_band_spectrum_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        BandSpectrum(**kwargs)


def test_photon_flux_integration_scales_linearly_with_N0():
    band = (1.0, 1000.0)
    base = BandSpectrum(alpha=-1.0, beta=-2.5, epeak_keV=300.0, N0=1.0)
    scaled = BandSpectrum(alpha=-1.0, beta=-2.5, epeak_keV=300.0, N0=3.0)

    assert scaled.photon_flux(band) == pytest.approx(3.0 * base.photon_flux(band), rel=1e-10)


def test_energy_flux_integration_uses_kev_to_erg_conversion():
    spectrum = BandSpectrum(alpha=-1.0, beta=-2.5, epeak_keV=300.0)
    band = (10.0, 20.0)

    energy_flux = spectrum.energy_flux(band, n_grid=8192)
    manual = spectrum.N0 * 0.0
    energies = np.logspace(np.log10(band[0]), np.log10(band[1]), 8192)
    manual = np.trapezoid(energies * spectrum.evaluate(energies) * KEV_TO_ERG, energies)

    assert energy_flux == pytest.approx(manual, rel=1e-12)


def test_renormalize_to_photon_flux():
    spectrum = BandSpectrum(alpha=-1.0, beta=-2.5, epeak_keV=300.0)
    normalized = spectrum.renormalized_to_photon_flux(2.0, (1.0, 1000.0))

    assert normalized.photon_flux((1.0, 1000.0)) == pytest.approx(2.0)
