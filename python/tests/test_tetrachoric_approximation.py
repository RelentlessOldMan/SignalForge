"""The tetrachoric approximation (ADR 0492)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_odds_ratio_formula_and_is_symmetric() -> None:
    rng = np.random.default_rng(255)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [0.0, 1.0]
        v = sf.tetrachoric_approximation(t, d)
        assert v == pytest.approx(
            math.cos(math.pi / (1.0 + math.sqrt(sf.diagnostic_odds_ratio(t, d)))), abs=1e-13
        )
        assert sf.tetrachoric_approximation(d, t) == pytest.approx(v, abs=1e-15)
        assert -1.0 <= v < 1.0


def test_rejects_records_that_disagree_one_way_only() -> None:
    with pytest.raises(ValueError):
        sf.tetrachoric_approximation([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0])
