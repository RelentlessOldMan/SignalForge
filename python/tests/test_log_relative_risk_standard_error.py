"""The standard error of the log relative risk (ADR 0499)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_delta_method_formula() -> None:
    rng = np.random.default_rng(262)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        tp, fn = float(np.sum(t * d)), float(np.sum(t * (1 - d)))
        fp, tn = float(np.sum((1 - t) * d)), float(np.sum((1 - t) * (1 - d)))
        want = math.sqrt(1 / tp - 1 / (tp + fp) + 1 / fn - 1 / (fn + tn))
        assert sf.log_relative_risk_standard_error(t, d) == pytest.approx(want, rel=1e-13)


def test_rejects_a_table_with_no_true_positive() -> None:
    with pytest.raises(ValueError):
        sf.log_relative_risk_standard_error([1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0])
