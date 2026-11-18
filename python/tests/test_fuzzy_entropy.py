"""Fuzzy entropy (ADR 0339)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_less_regular_than_a_sine() -> None:
    n = np.arange(400)
    sine = np.sin(2 * np.pi * n / 40)
    noise = np.random.default_rng(32).standard_normal(400)
    assert sf.fuzzy_entropy(sine, 2, 0.2) < sf.fuzzy_entropy(noise, 2, 0.2)


def test_an_offset_and_a_trend_change_nothing() -> None:
    # Each template's own mean is removed; a linear trend shifts every template the same way.
    x = np.random.default_rng(33).standard_normal(200)
    trend = x + 5.0 + 0.01 * np.arange(200)
    assert sf.fuzzy_entropy(trend, 2, 0.3) == pytest.approx(sf.fuzzy_entropy(x, 2, 0.3), rel=1e-12)


def test_is_defined_where_sample_entropy_is_not() -> None:
    x = [0.0, 4.0, 8.0, 12.0, 17.0]
    with pytest.raises(ValueError):
        sf.sample_entropy(x, 1, 1.0)
    assert np.isfinite(sf.fuzzy_entropy(x, 1, 1.0))


def test_rejects_a_zero_width() -> None:
    with pytest.raises(ValueError):
        sf.fuzzy_entropy([0.0, 1.0, 2.0, 3.0], 1, 0.0)
