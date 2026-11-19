"""The balanced accuracy (ADR 0396)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_youden_j_shifted_to_the_unit_interval() -> None:
    rng = np.random.default_rng(130)
    truth = (rng.random(300) < 0.2).astype(float)
    decision = np.where(rng.random(300) < 0.7, truth, 1 - truth)
    expected = (sf.youden_j(truth, decision) + 1) / 2
    assert sf.balanced_accuracy(truth, decision) == pytest.approx(expected, abs=1e-15)


def test_is_the_mean_of_the_two_rates() -> None:
    rng = np.random.default_rng(131)
    truth = (rng.random(200) < 0.5).astype(float)
    decision = np.where(rng.random(200) < 0.6, truth, 1 - truth)
    t, d = truth == 1, decision == 1
    expected = (np.mean(d[t]) + np.mean(~d[~t])) / 2
    assert sf.balanced_accuracy(truth, decision) == pytest.approx(expected, abs=1e-15)


def test_rejects_a_truth_without_a_one() -> None:
    with pytest.raises(ValueError):
        sf.balanced_accuracy([0.0, 0.0], [1.0, 0.0])
