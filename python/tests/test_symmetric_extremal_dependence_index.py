"""The symmetric extremal dependence index (ADR 0491)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_rate_formula_and_survives_complementing_both_records() -> None:
    rng = np.random.default_rng(254)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:4] = [1.0, 1.0, 0.0, 0.0]
        d[:4] = [1.0, 0.0, 1.0, 0.0]
        h = float(np.sum(t * d)) / float(np.sum(t))
        f = float(np.sum((1 - t) * d)) / float(np.sum(1 - t))
        lf, lg, lh, lm = math.log(f), math.log(1 - f), math.log(h), math.log(1 - h)
        v = sf.symmetric_extremal_dependence_index(t, d)
        assert v == pytest.approx((lf - lh - lg + lm) / (lf + lh + lg + lm), abs=1e-13)
        assert sf.symmetric_extremal_dependence_index(1 - t, 1 - d) == pytest.approx(v, abs=1e-13)
        assert -1.0 - 1e-15 <= v <= 1.0 + 1e-15


def test_rejects_a_table_with_a_zero_cell() -> None:
    with pytest.raises(ValueError):
        sf.symmetric_extremal_dependence_index([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0])
