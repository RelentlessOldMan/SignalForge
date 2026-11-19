"""Biweight midcorrelation (ADR 0373)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_resists_outliers_that_flip_pearson() -> None:
    rng = np.random.default_rng(88)
    x = rng.standard_normal(200)
    y = x + 0.3 * rng.standard_normal(200)
    x[:4] = [40.0, 41.0, 42.0, 43.0]
    y[:4] = [-40.0, -41.0, -42.0, -43.0]
    assert sf.pearson_correlation(x, y) < 0
    assert sf.biweight_midcorrelation(x, y) > 0.9


def test_is_near_pearson_for_clean_normal_data() -> None:
    rng = np.random.default_rng(89)
    x = rng.standard_normal(5000)
    y = 0.5 * x + rng.standard_normal(5000)
    assert sf.biweight_midcorrelation(x, y) == pytest.approx(sf.pearson_correlation(x, y), abs=0.02)


def test_rejects_a_zero_mad() -> None:
    with pytest.raises(ValueError):
        sf.biweight_midcorrelation([1.0, 1.0, 2.0], [1.0, 2.0, 3.0])
