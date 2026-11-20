"""Loevinger's H (ADR 0441)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_phi_over_the_largest_phi() -> None:
    rng = np.random.default_rng(204)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        pa, pb = np.mean(t), np.mean(d)
        lo, hi = min(pa, pb), max(pa, pb)
        phi_max = math.sqrt(lo * (1 - hi) / (hi * (1 - lo)))
        want = sf.matthews_correlation(t, d) / phi_max
        assert sf.loevinger_h(t, d) == pytest.approx(want, rel=1e-12, abs=1e-14)


def test_is_one_when_one_record_lies_inside_the_other() -> None:
    assert sf.loevinger_h([1.0, 1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 1.0, 0.0, 0.0]) == 1.0


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.loevinger_h([1.0, 1.0], [1.0, 0.0])
