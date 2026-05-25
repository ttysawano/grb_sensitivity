from copy import deepcopy

import pytest

from grb_sensitivity.config_io import load_and_validate
from grb_sensitivity.config_schema import ConfigError, default_config, validate_config


def test_example_curve_config_validates():
    result = load_and_validate("examples/example_curve.yaml")

    assert result.config["mode"] == "curve"
    assert result.warnings == []


def test_missing_response_quantity_is_rejected():
    config = default_config(response_quantity="efficiency")
    broken = deepcopy(config)
    broken["detector"]["response"].pop("quantity")

    with pytest.raises(ConfigError, match="detector.response.quantity is required"):
        validate_config(broken)


def test_null_response_quantity_is_rejected():
    config = default_config(response_quantity=None)

    with pytest.raises(ConfigError, match="response.quantity is required"):
        validate_config(config)


def test_invalid_band_parameters_are_rejected():
    config = default_config(response_quantity="efficiency")
    config["spectrum"]["alpha"] = -2.1

    with pytest.raises(ConfigError, match="alpha"):
        validate_config(config)
