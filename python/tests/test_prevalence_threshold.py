"""The prevalence threshold (ADR 0487)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_rate_formula_and_lies_in_the_unit_interval() -> None:
    rng = np.random.default_rng(250)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:3] = [1.0, 0.0, 0.0]
        d[:3] = [1.0, 0.0, 1.0]
        tpr = float(np.sum(t * d)) / float(np.sum(t))
        fpr = float(np.sum((1 - t) * d)) / float(np.sum(1 - t))
        if tpr == fpr:
            continue
        v = sf.prevalence_threshold(t, d)
        assert v == pytest.approx((math.sqrt(tpr * fpr) - fpr) / (tpr - fpr), abs=1e-13)
        assert -1e-15 <= v <= 1.0 + 1e-15


def test_rejects_equal_rates() -> None:
    with pytest.raises(ValueError):
        sf.prevalence_threshold([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0])
