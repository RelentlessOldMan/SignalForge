"""Multiscale entropy (ADR 0338)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_scale_one_is_sample_entropy() -> None:
    x = np.random.default_rng(30).standard_normal(400)
    assert sf.multiscale_entropy(x, 2, 0.2, [1])[0] == sf.sample_entropy(x, 2, 0.2)


def test_white_noise_falls_with_scale() -> None:
    # Coarse-graining white noise shrinks its spread by sqrt(scale) while r stays fixed.
    x = np.random.default_rng(31).standard_normal(3000)
    e = sf.multiscale_entropy(x, 2, 0.15, [1, 4, 10])
    assert e[0] > e[1] > e[2]


def test_rejects_too_large_a_scale() -> None:
    with pytest.raises(ValueError):
        sf.multiscale_entropy(np.zeros(10), 2, 0.1, [3])
