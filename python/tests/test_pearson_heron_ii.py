"""The Pearson-Heron II coefficient (ADR 0443)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_sine_of_a_scaled_yules_y() -> None:
    rng = np.random.default_rng(206)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        want = math.sin(math.pi * sf.yule_y(t, d) / 2)
        assert sf.pearson_heron_ii(t, d) == pytest.approx(want, rel=1e-13, abs=1e-14)


def test_changes_sign_when_the_decision_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    got = sf.pearson_heron_ii(t, 1 - d)
    assert got == pytest.approx(-sf.pearson_heron_ii(t, d), rel=1e-14)


def test_rejects_a_table_with_both_products_zero() -> None:
    with pytest.raises(ValueError):
        sf.pearson_heron_ii([1.0, 1.0, 1.0], [1.0, 0.0, 1.0])
