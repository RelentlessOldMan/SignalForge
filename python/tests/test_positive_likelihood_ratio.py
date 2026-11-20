"""The positive likelihood ratio (ADR 0482)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_true_positive_rate_over_the_false_positive_rate() -> None:
    rng = np.random.default_rng(245)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 1.0]
        tpr = float(np.sum(t * d)) / float(np.sum(t))
        fpr = float(np.sum((1 - t) * d)) / float(np.sum(1 - t))
        v = sf.positive_likelihood_ratio(t, d)
        assert v == pytest.approx(tpr / fpr, rel=1e-14)
        assert v >= 0.0


def test_rejects_a_decision_with_no_false_positive() -> None:
    with pytest.raises(ValueError):
        sf.positive_likelihood_ratio([1.0, 0.0], [1.0, 0.0])
