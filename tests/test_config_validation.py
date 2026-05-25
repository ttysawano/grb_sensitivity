from copy import deepcopy
import pytest
import yaml

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


def test_missing_response_csv_file_is_rejected(tmp_path):
    config = default_config(response_quantity="efficiency")
    config["detector"]["response"]["path"] = "missing.csv"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ConfigError, match="response CSV file was not found"):
        load_and_validate(config_path)


def test_response_csv_zero_energy_message_suggests_fix(tmp_path):
    response_path = tmp_path / "response.csv"
    response_path.write_text("energy_keV,efficiency\n0,0.5\n10,0.6\n", encoding="utf-8")
    config = default_config(response_quantity="efficiency")
    config["detector"]["response"]["path"] = "response.csv"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ConfigError, match="zero or negative energy values"):
        load_and_validate(config_path)


def test_response_csv_zero_response_message_suggests_fix(tmp_path):
    response_path = tmp_path / "response.csv"
    response_path.write_text("energy_keV,efficiency\n1,0\n10,0.6\n", encoding="utf-8")
    config = default_config(response_quantity="efficiency")
    config["detector"]["response"]["path"] = "response.csv"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ConfigError, match="zero or negative response values"):
        load_and_validate(config_path)


def test_invalid_trigger_band_message_names_e1_e2():
    config = default_config(response_quantity="efficiency")
    config["detector"]["trigger"]["energy_band_keV"] = [1000.0, 10.0]

    with pytest.raises(ConfigError, match="E_2 must be greater than lower energy E_1"):
        validate_config(config)


def test_invalid_aperture_message_suggests_disable_cxb():
    config = default_config(response_quantity="efficiency")
    config["detector"]["aperture_solid_angle_sr"] = 0.0

    with pytest.raises(ConfigError, match="disable background.cxb.enabled"):
        validate_config(config)
