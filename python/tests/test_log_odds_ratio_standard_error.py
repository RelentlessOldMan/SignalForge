"""The standard error of the log odds ratio (ADR 0493)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_reciprocal_sum_and_is_symmetric() -> None:
    rng = np.random.default_rng(256)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:4] = [1.0, 1.0, 0.0, 0.0]
        d[:4] = [1.0, 0.0, 1.0, 0.0]
        cells = [np.sum(t * d), np.sum(t * (1 - d)), np.sum((1 - t) * d), np.sum((1 - t) * (1 - d))]
        v = sf.log_odds_ratio_standard_error(t, d)
        assert v == pytest.approx(math.sqrt(sum(1.0 / float(c) for c in cells)), rel=1e-14)
        assert sf.log_odds_ratio_standard_error(d, t) == v


def test_rejects_a_table_with_a_zero_cell() -> None:
    with pytest.raises(ValueError):
        sf.log_odds_ratio_standard_error([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
