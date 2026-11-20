"""The extremal dependence index (ADR 0490)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_rate_formula_and_lies_from_minus_one_to_one() -> None:
    rng = np.random.default_rng(253)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:3] = [1.0, 0.0, 0.0]
        d[:3] = [1.0, 1.0, 0.0]
        h = float(np.sum(t * d)) / float(np.sum(t))
        f = float(np.sum((1 - t) * d)) / float(np.sum(1 - t))
        v = sf.extremal_dependence_index(t, d)
        want = (math.log(f) - math.log(h)) / (math.log(f) + math.log(h))
        assert v == pytest.approx(want, abs=1e-13)
        assert -1.0 - 1e-15 <= v <= 1.0 + 1e-15


def test_rejects_a_decision_of_all_ones() -> None:
    with pytest.raises(ValueError):
        sf.extremal_dependence_index([1.0, 0.0], [1.0, 1.0])
