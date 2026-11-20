"""The G statistic of two binary records (ADR 0481)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_2n_times_the_mutual_information() -> None:
    rng = np.random.default_rng(244)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.binary_g_statistic(t, d)
        assert v == pytest.approx(50 * sf.binary_mutual_information(t, d), abs=1e-12)
        assert v == pytest.approx(sf.binary_g_statistic(d, t), abs=1e-12)
        assert v >= -1e-12


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.binary_g_statistic([0.0, 1.0], [1.0])
