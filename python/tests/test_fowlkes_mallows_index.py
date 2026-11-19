"""The Fowlkes-Mallows index (ADR 0389)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_geometric_mean_of_precision_and_recall() -> None:
    rng = np.random.default_rng(118)
    truth = (rng.random(300) < 0.3).astype(float)
    decision = np.where(rng.random(300) < 0.8, truth, 1 - truth)
    tp = np.sum((truth == 1) & (decision == 1))
    expected = np.sqrt(tp / np.sum(decision == 1) * (tp / np.sum(truth == 1)))
    assert sf.fowlkes_mallows_index(truth, decision) == pytest.approx(expected, abs=1e-14)


def test_is_at_least_the_f1_score() -> None:
    rng = np.random.default_rng(119)
    truth = (rng.random(200) < 0.4).astype(float)
    decision = np.where(rng.random(200) < 0.7, truth, 1.0)
    assert sf.fowlkes_mallows_index(truth, decision) >= sf.f1_score(truth, decision)


def test_rejects_a_record_without_a_one() -> None:
    with pytest.raises(ValueError):
        sf.fowlkes_mallows_index([1.0, 0.0], [0.0, 0.0])
