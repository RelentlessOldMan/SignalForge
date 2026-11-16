"""Energy-time curve (conventions: Energy-time curve; ADR 0186)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_peak_is_zero_db() -> None:
    h = np.random.default_rng(33).standard_normal(500) * 0.99 ** np.arange(500)
    assert np.max(sf.energy_time_curve(h)) == 0.0


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.energy_time_curve(np.array([1.0 + 1.0j, 0.0]))
