"""Cohen's d (ADR 0397)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_difference_over_the_pooled_deviation() -> None:
    rng = np.random.default_rng(132)
    x, y = rng.normal(1.0, 2.0, 50), rng.normal(0.0, 2.0, 70)
    pooled = ((x.size - 1) * np.var(x, ddof=1) + (y.size - 1) * np.var(y, ddof=1)) / (
        x.size + y.size - 2
    )
    expected = (np.mean(x) - np.mean(y)) / np.sqrt(pooled)
    assert sf.cohen_d(x, y) == pytest.approx(expected, rel=1e-12)


def test_is_unchanged_by_a_common_affine_map() -> None:
    rng = np.random.default_rng(133)
    x, y = rng.normal(0.5, 1.0, 30), rng.normal(0.0, 1.0, 30)
    assert sf.cohen_d(3 * x + 7, 3 * y + 7) == pytest.approx(sf.cohen_d(x, y), rel=1e-12)


def test_rejects_no_spread() -> None:
    with pytest.raises(ValueError):
        sf.cohen_d([1.0, 1.0], [2.0, 2.0])
