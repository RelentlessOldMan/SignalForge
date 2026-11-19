"""The average precision (ADR 0394)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_precision_at_each_positive_without_ties() -> None:
    rng = np.random.default_rng(127)
    truth = (rng.random(300) < 0.25).astype(float)
    score = rng.normal(truth, 1.0)
    ranked = truth[np.argsort(-score)]
    hits = np.cumsum(ranked)
    expected = np.mean((hits / np.arange(1, ranked.size + 1))[ranked == 1])
    assert sf.average_precision(truth, score) == pytest.approx(expected, rel=1e-13)


def test_does_not_depend_on_the_order_of_ties() -> None:
    truth = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
    score = np.array([2.0, 2.0, 1.0, 1.0, 1.0, 0.0])
    flip = np.arange(5, -1, -1)
    assert sf.average_precision(truth[flip], score[flip]) == sf.average_precision(truth, score)


def test_rejects_no_positive() -> None:
    with pytest.raises(ValueError):
        sf.average_precision([0.0, 0.0], [0.2, 0.4])
