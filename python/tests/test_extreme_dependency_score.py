"""The extreme dependency score (ADR 0489)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_log_formula_and_lies_from_minus_one_to_one() -> None:
    rng = np.random.default_rng(252)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[0] = 1.0
        n = float(t.size)
        base = float(np.sum(t)) / n
        hits = float(np.sum(t * d)) / n
        v = sf.extreme_dependency_score(t, d)
        assert v == pytest.approx(2.0 * math.log(base) / math.log(hits) - 1.0, abs=1e-13)
        assert -1.0 - 1e-15 <= v <= 1.0 + 1e-15


def test_rejects_records_with_no_shared_one() -> None:
    with pytest.raises(ValueError):
        sf.extreme_dependency_score([1.0, 0.0], [0.0, 1.0])
