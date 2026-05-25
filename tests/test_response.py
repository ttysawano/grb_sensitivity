import numpy as np
import pandas as pd
import pytest

from grb_sensitivity.response import DetectorResponse


def test_response_interpolation_reproduces_tabulated_points():
    response = DetectorResponse(
        energy_keV=np.array([10.0, 100.0, 1000.0]),
        values=np.array([0.2, 0.8, 0.4]),
        quantity="efficiency",
    )

    assert response.evaluate(np.array([10.0, 100.0, 1000.0])) == pytest.approx([0.2, 0.8, 0.4])


def test_response_interpolation_by_name_and_one_based_column_number(tmp_path):
    path = tmp_path / "response.csv"
    pd.DataFrame({"energy_keV": [10.0, 100.0], "efficiency": [0.2, 0.8]}).to_csv(path, index=False)

    by_name = DetectorResponse.from_csv(path, quantity="efficiency", energy_column="energy_keV", value_column="efficiency")
    by_number = DetectorResponse.from_csv(path, quantity="efficiency", energy_column=1, value_column=2)

    assert by_name.evaluate(10.0) == pytest.approx(0.2)
    assert by_number.evaluate(100.0) == pytest.approx(0.8)


@pytest.mark.parametrize(
    "energy, values",
    [
        ([0.0, 100.0], [0.2, 0.8]),
        ([10.0, 100.0], [0.0, 0.8]),
        ([10.0, 100.0], [-0.1, 0.8]),
    ],
)
def test_response_rejects_zero_and_negative_values(energy, values):
    with pytest.raises(ValueError, match="positive"):
        DetectorResponse(energy_keV=np.array(energy), values=np.array(values), quantity="efficiency")


def test_response_powerlaw_extrapolation_warns():
    response = DetectorResponse(
        energy_keV=np.array([10.0, 100.0]),
        values=np.array([1.0, 10.0]),
        quantity="effective_area_cm2",
    )

    with pytest.warns(RuntimeWarning, match="extrapolated above"):
        assert response.evaluate(1000.0) == pytest.approx(100.0)
