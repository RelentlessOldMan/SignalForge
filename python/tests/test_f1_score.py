"""The F1 score (ADR 0386)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_harmonic_mean_of_precision_and_recall() -> None:
    rng = np.random.default_rng(115)
    truth = (rng.random(400) < 0.3).astype(float)
    decision = np.where(rng.random(400) < 0.8, truth, 1 - truth)
    tp = np.sum((truth == 1) & (decision == 1))
    precision = tp / np.sum(decision == 1)
    recall = tp / np.sum(truth == 1)
    expected = 2 * precision * recall / (precision + recall)
    assert sf.f1_score(truth, decision) == pytest.approx(expected, abs=1e-14)


def test_ignores_the_true_negatives() -> None:
    truth = [1.0, 1.0, 0.0]
    decision = [1.0, 0.0, 1.0]
    assert sf.f1_score(truth + [0.0] * 50, decision + [0.0] * 50) == sf.f1_score(truth, decision)


def test_rejects_no_positive() -> None:
    with pytest.raises(ValueError):
        sf.f1_score([0.0, 0.0], [0.0, 0.0])
