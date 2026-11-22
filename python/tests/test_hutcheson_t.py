"""Hutcheson's t (ADR 0557)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _entropy(x: np.ndarray) -> float:
    p = x[x > 0] / np.sum(x)
    return float(-np.sum(p * np.log(p)))


def test_matches_the_entropies_and_variances() -> None:
    rng = np.random.default_rng(320)
    for n in range(1, 30):
        a = rng.integers(0, 10, n).astype(float)
        b = rng.integers(0, 10, n + 3).astype(float)
        a[0] += 2.0
        b[0] += 1.0
        b[1] += 1.0
        spread = sf.hutcheson_variance(a) + sf.hutcheson_variance(b)
        expected = (_entropy(a) - _entropy(b)) / math.sqrt(spread)
        t = sf.hutcheson_t(a, b)
        assert t == pytest.approx(expected, rel=1e-11, abs=1e-12)
        assert sf.hutcheson_t(b, a) == pytest.approx(-t, rel=1e-13, abs=1e-15)


def test_rejects_bad_records() -> None:
    for a, b in [([], [1.0]), ([1.0], [-1.0]), ([0.0], [1.0, 2.0]), ([1.5], [1.0, 2.0])]:
        with pytest.raises(ValueError):
            sf.hutcheson_t(a, b)
    with pytest.raises(ValueError, match="single kind"):
        sf.hutcheson_t([4.0], [0.0, 3.0])
