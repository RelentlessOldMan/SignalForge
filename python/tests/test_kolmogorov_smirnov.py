"""The two-sample Kolmogorov-Smirnov statistic (ADR 0402)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_largest_gap_on_a_fine_grid() -> None:
    rng = np.random.default_rng(141)
    x, y = np.round(rng.normal(0.4, 1.0, 50), 1), np.round(rng.normal(0.0, 2.0, 35), 1)
    t = np.concatenate([x, y])[:, None]
    expected = np.max(np.abs(np.mean(x <= t, axis=1) - np.mean(y <= t, axis=1)))
    assert sf.kolmogorov_smirnov(x, y) == pytest.approx(expected, abs=1e-15)


def test_is_symmetric_and_rank_only() -> None:
    rng = np.random.default_rng(142)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 20)
    assert sf.kolmogorov_smirnov(y, x) == sf.kolmogorov_smirnov(x, y)
    assert sf.kolmogorov_smirnov(np.exp(x), np.exp(y)) == sf.kolmogorov_smirnov(x, y)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.kolmogorov_smirnov([1.0], [])
