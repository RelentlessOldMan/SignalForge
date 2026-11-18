"""SVD entropy (ADR 0342)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_fills_two_directions() -> None:
    # A zero-mean sine embedded in 4 dimensions has rank 2 and, over whole periods with a
    # quarter-period delay, two equal singular values: ln 2 / ln 4 = 1/2.
    x = np.sin(2 * np.pi * np.arange(400) / 20)
    assert sf.svd_entropy(x, 4, 5) == pytest.approx(math.log(2) / math.log(4), abs=0.02)


def test_noise_is_close_to_one() -> None:
    x = np.random.default_rng(39).standard_normal(4000)
    assert sf.svd_entropy(x, 6) > 0.98


def test_scale_changes_nothing() -> None:
    x = np.random.default_rng(40).standard_normal(300)
    assert sf.svd_entropy(-3 * x, 4) == pytest.approx(sf.svd_entropy(x, 4), rel=1e-12)


def test_rejects_zeros() -> None:
    with pytest.raises(ValueError):
        sf.svd_entropy(np.zeros(10), 3)
