"""The Haldane log odds ratio (ADR 0494)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_corrected_cells_and_flips_sign_with_the_decision() -> None:
    rng = np.random.default_rng(257)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        tp, fn = np.sum(t * d) + 0.5, np.sum(t * (1 - d)) + 0.5
        fp, tn = np.sum((1 - t) * d) + 0.5, np.sum((1 - t) * (1 - d)) + 0.5
        v = sf.haldane_log_odds_ratio(t, d)
        assert v == pytest.approx(math.log(float(tp * tn / (fn * fp))), abs=1e-14)
        assert sf.haldane_log_odds_ratio(t, 1 - d) == pytest.approx(-v, abs=1e-14)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.haldane_log_odds_ratio([1.0, 0.0], [1.0])
