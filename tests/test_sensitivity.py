import pytest

from grb_sensitivity.background import internal_background_counts
from grb_sensitivity.detector import make_flat_efficiency_detector
from grb_sensitivity.sensitivity import significance_for_peak_flux, threshold_peak_photon_flux


def test_internal_background_counts_equal_rate_times_time():
    assert internal_background_counts(R_int_cps=12.5, Delta_t=4.0) == pytest.approx(50.0)


def test_threshold_flux_decreases_when_detector_area_increases():
    small = make_flat_efficiency_detector(geometric_area_cm2=100.0)
    large = make_flat_efficiency_detector(geometric_area_cm2=400.0)

    common = dict(
        alpha=-1.0,
        beta=-2.5,
        epeak_keV=300.0,
        epivot_keV=100.0,
        trigger_band_keV=(10.0, 1000.0),
        reference_band_keV=(1.0, 1000.0),
        Delta_t=1.0,
        sigma_0=8.0,
        R_int_cps=100.0,
        cxb_enabled=False,
        n_grid=2048,
    )

    small_result = threshold_peak_photon_flux(detector=small, **common)
    large_result = threshold_peak_photon_flux(detector=large, **common)

    assert large_result.threshold_photon_flux_ph_cm2_s < small_result.threshold_photon_flux_ph_cm2_s


def test_significance_increases_when_peak_flux_increases():
    detector = make_flat_efficiency_detector(geometric_area_cm2=100.0)
    common = dict(
        alpha=-1.0,
        beta=-2.5,
        epeak_keV=300.0,
        epivot_keV=100.0,
        peak_flux_band_keV=(1.0, 1000.0),
        detector=detector,
        trigger_band_keV=(10.0, 1000.0),
        Delta_t=1.0,
        R_int_cps=100.0,
        cxb_enabled=False,
        n_grid=2048,
    )

    low = significance_for_peak_flux(peak_flux_ph_cm2_s=1.0, **common)
    high = significance_for_peak_flux(peak_flux_ph_cm2_s=2.0, **common)

    assert high > low
    assert high == pytest.approx(2.0 * low, rel=1e-10)
