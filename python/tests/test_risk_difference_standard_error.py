"""The standard error of the risk difference (ADR 0502)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_wald_error_and_ignores_complementing_the_truth() -> None:
    rng = np.random.default_rng(265)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        p1, n1 = float(np.mean(t[d == 1])), float(np.sum(d == 1))
        p0, n0 = float(np.mean(t[d == 0])), float(np.sum(d == 0))
        want = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
        v = sf.risk_difference_standard_error(t, d)
        assert v == pytest.approx(want, rel=1e-13, abs=1e-15)
        assert sf.risk_difference_standard_error(1 - t, d) == pytest.approx(v, rel=1e-15)


def test_rejects_a_decision_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.risk_difference_standard_error([1.0, 0.0, 1.0], [0.0, 0.0, 0.0])
