"""ERB scale (conventions: ERB scale; ADR 0160)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_round_trip() -> None:
    f = np.linspace(0.0, 20000.0, 41)
    assert sf.erb_rate_to_hz(sf.hz_to_erb_rate(f)) == pytest.approx(f, abs=1e-9)


def test_rate_slope_times_bandwidth_is_the_constant_ratio() -> None:
    f, h = np.array([100.0, 1000.0, 5000.0]), 1e-3
    slope = (np.asarray(sf.hz_to_erb_rate(f + h)) - np.asarray(sf.hz_to_erb_rate(f - h))) / (2 * h)
    ratio = 21.4 * 24.7 * 4.37 / (1000 * math.log(10))  # about 1.0032 (ADR 0160)
    assert slope * np.asarray(sf.erb_bandwidth(f)) == pytest.approx(ratio, rel=1e-7)
