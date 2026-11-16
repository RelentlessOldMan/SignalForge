"""A and C weightings (conventions: Frequency weightings; ADR 0164)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_exactly_zero_at_1khz_and_minus_inf_at_dc() -> None:
    assert sf.a_weighting(1000.0) == 0.0 and sf.c_weighting(1000.0) == 0.0
    assert sf.a_weighting(0.0) == -math.inf and sf.c_weighting(0.0) == -math.inf


def test_arrays_and_the_standard_table_at_base_ten_frequencies() -> None:
    f = 1000 * 10 ** (np.array([-10, 3, 10]) / 10)
    assert np.asarray(sf.a_weighting(f)) == pytest.approx([-19.1, 1.2, -2.5], abs=0.05)
    assert np.asarray(sf.c_weighting(f)) == pytest.approx([-0.3, -0.2, -4.4], abs=0.05)


def test_no_overflow_at_huge_frequencies() -> None:
    assert math.isfinite(float(sf.a_weighting(1e200)))
    assert math.isfinite(float(sf.c_weighting(1e200)))
