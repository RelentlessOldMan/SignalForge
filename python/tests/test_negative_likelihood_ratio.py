"""The negative likelihood ratio (ADR 0483)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_false_negative_rate_over_the_true_negative_rate() -> None:
    rng = np.random.default_rng(246)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [0.0, 0.0]
        fnr = float(np.sum(t * (1 - d))) / float(np.sum(t))
        tnr = float(np.sum((1 - t) * (1 - d))) / float(np.sum(1 - t))
        v = sf.negative_likelihood_ratio(t, d)
        assert v == pytest.approx(fnr / tnr, rel=1e-14)
        assert v >= 0.0


def test_rejects_a_decision_with_no_true_negative() -> None:
    with pytest.raises(ValueError):
        sf.negative_likelihood_ratio([1.0, 0.0], [0.0, 1.0])
