"""Markedness (ADR 0395)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_youden_j_with_truth_and_decision_swapped() -> None:
    rng = np.random.default_rng(128)
    truth = (rng.random(300) < 0.35).astype(float)
    decision = np.where(rng.random(300) < 0.75, truth, 1 - truth)
    assert sf.markedness(truth, decision) == pytest.approx(sf.youden_j(decision, truth), abs=1e-15)


def test_with_informedness_gives_the_matthews_correlation() -> None:
    rng = np.random.default_rng(129)
    truth = (rng.random(300) < 0.4).astype(float)
    decision = np.where(rng.random(300) < 0.8, truth, 1 - truth)
    mk, j = sf.markedness(truth, decision), sf.youden_j(truth, decision)
    assert np.sqrt(mk * j) == pytest.approx(sf.matthews_correlation(truth, decision), rel=1e-13)


def test_rejects_a_decision_without_a_zero() -> None:
    with pytest.raises(ValueError):
        sf.markedness([1.0, 0.0], [1.0, 1.0])
