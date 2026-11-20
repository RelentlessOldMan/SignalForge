"""The log odds ratio (ADR 0480)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_of_the_diagnostic_odds_ratio() -> None:
    rng = np.random.default_rng(243)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:4] = [1.0, 1.0, 0.0, 0.0]
        d[:4] = [1.0, 0.0, 1.0, 0.0]
        v = sf.log_odds_ratio(t, d)
        assert v == pytest.approx(math.log(sf.diagnostic_odds_ratio(t, d)), abs=1e-14)
        assert v == sf.log_odds_ratio(d, t)
        assert sf.log_odds_ratio(t, 1.0 - d) == pytest.approx(-v, abs=1e-14)


def test_rejects_a_zero_cell() -> None:
    with pytest.raises(ValueError):
        sf.log_odds_ratio([1.0, 0.0, 1.0], [1.0, 1.0, 0.0])
