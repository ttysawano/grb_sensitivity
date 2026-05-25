"""Detector response CSV loading and log-log interpolation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import warnings

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DetectorResponse:
    """Tabulated detector response as efficiency or effective area.

    The tabulated values must be positive because v0.1 interpolates linearly in
    ``log(E)`` and ``log(value)``. A zero response policy is intentionally left
    out of v0.1 so accidental zeros do not silently become invalid logarithms.
    """

    energy_keV: np.ndarray
    values: np.ndarray
    quantity: str
    interpolation: str = "loglog"
    extrapolation: str = "powerlaw_with_warning"

    def __post_init__(self) -> None:
        energy = np.asarray(self.energy_keV, dtype=float)
        values = np.asarray(self.values, dtype=float)
        if self.quantity not in {"efficiency", "effective_area_cm2"}:
            raise ValueError("response.quantity must be 'efficiency' or 'effective_area_cm2'.")
        if self.interpolation != "loglog":
            raise ValueError("Only loglog interpolation is implemented in v0.1.")
        if self.extrapolation != "powerlaw_with_warning":
            raise ValueError("Only powerlaw_with_warning extrapolation is implemented in v0.1.")
        if energy.ndim != 1 or values.ndim != 1 or len(energy) != len(values):
            raise ValueError("response energy and value arrays must be one-dimensional arrays of equal length.")
        if len(energy) < 2:
            raise ValueError("response CSV must contain at least two rows.")
        if np.any(energy <= 0):
            raise ValueError("response energy values must be positive for log-log interpolation.")
        if np.any(values <= 0):
            raise ValueError("response values must be positive for log-log interpolation.")

        order = np.argsort(energy)
        sorted_energy = energy[order]
        sorted_values = values[order]
        if np.any(np.diff(sorted_energy) <= 0):
            raise ValueError("response energy values must be unique.")

        object.__setattr__(self, "energy_keV", sorted_energy)
        object.__setattr__(self, "values", sorted_values)

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        *,
        quantity: str,
        energy_column: int | str = 1,
        value_column: int | str = 2,
        csv_has_header: bool = True,
        interpolation: str = "loglog",
        extrapolation: str = "powerlaw_with_warning",
    ) -> "DetectorResponse":
        """Load a response CSV.

        Column numbers are 1-based to match spreadsheet counting in the user
        YAML. They are converted to pandas' 0-based column positions here.
        """

        header = 0 if csv_has_header else None
        frame = pd.read_csv(path, header=header)
        energy = _select_column(frame, energy_column, "energy_column")
        values = _select_column(frame, value_column, "value_column")
        return cls(
            energy_keV=np.asarray(energy, dtype=float),
            values=np.asarray(values, dtype=float),
            quantity=quantity,
            interpolation=interpolation,
            extrapolation=extrapolation,
        )

    def evaluate(self, E_keV):
        """Evaluate response at photon energy ``E_keV``.

        Interpolation is linear in log-log space. Outside the tabulated energy
        range, the endpoint log-log slope is used, which is a local power-law
        extrapolation. A warning is emitted so students notice when their
        trigger band extends beyond the response CSV.
        """

        E = np.asarray(E_keV, dtype=float)
        if np.any(E <= 0):
            raise ValueError("response evaluation energies must be positive.")

        log_E_table = np.log(self.energy_keV)
        log_y_table = np.log(self.values)
        log_E = np.log(E)

        log_y = np.interp(log_E, log_E_table, log_y_table)

        below = log_E < log_E_table[0]
        above = log_E > log_E_table[-1]
        if np.any(below):
            warnings.warn(
                "Detector response is being extrapolated below the CSV energy range using the endpoint power-law slope.",
                RuntimeWarning,
                stacklevel=2,
            )
            slope = (log_y_table[1] - log_y_table[0]) / (log_E_table[1] - log_E_table[0])
            log_y = np.where(below, log_y_table[0] + slope * (log_E - log_E_table[0]), log_y)
        if np.any(above):
            warnings.warn(
                "Detector response is being extrapolated above the CSV energy range using the endpoint power-law slope.",
                RuntimeWarning,
                stacklevel=2,
            )
            slope = (log_y_table[-1] - log_y_table[-2]) / (log_E_table[-1] - log_E_table[-2])
            log_y = np.where(above, log_y_table[-1] + slope * (log_E - log_E_table[-1]), log_y)

        y = np.exp(log_y)
        if np.isscalar(E_keV):
            return float(y)
        return y

    __call__ = evaluate


def _select_column(frame: pd.DataFrame, column: int | str, field_name: str) -> pd.Series:
    """Select a CSV column by name or 1-based column number."""

    column_spec: Any = column
    if isinstance(column_spec, str) and column_spec.strip().isdigit():
        column_spec = int(column_spec)
    if isinstance(column_spec, int):
        if column_spec < 1 or column_spec > len(frame.columns):
            raise ValueError(f"{field_name} column number {column_spec} is outside the CSV column range.")
        return frame.iloc[:, column_spec - 1]
    if column_spec not in frame.columns:
        raise ValueError(f"{field_name} column '{column_spec}' was not found in the response CSV.")
    return frame[column_spec]
