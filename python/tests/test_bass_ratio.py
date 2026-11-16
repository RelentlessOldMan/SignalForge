"""Bass and treble ratio (conventions: Bass and treble ratio; ADR 0180)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_ratios_ignore_a_common_scale() -> None:
    t = np.array([2.1, 1.9, 1.7, 1.6, 1.4, 1.1])
    assert sf.bass_ratio(3 * t) == pytest.approx(sf.bass_ratio(t), rel=1e-15)
    assert sf.treble_ratio(3 * t) == pytest.approx(sf.treble_ratio(t), rel=1e-15)


def test_two_dimensional_times_are_rejected() -> None:
    with pytest.raises(ValueError):
        sf.bass_ratio(np.ones((2, 6)))
