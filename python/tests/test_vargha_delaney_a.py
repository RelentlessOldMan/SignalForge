"""The Vargha-Delaney A (ADR 0401)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_cliff_delta_moved_to_a_probability() -> None:
    rng = np.random.default_rng(139)
    x, y = np.round(rng.normal(0.5, 1.0, 60), 1), np.round(rng.normal(0.0, 1.0, 45), 1)
    expected = (sf.cliff_delta(x, y) + 1) / 2
    assert sf.vargha_delaney_a(x, y) == pytest.approx(expected, abs=1e-15)


def test_is_the_roc_auc_of_the_pooled_samples() -> None:
    rng = np.random.default_rng(140)
    x, y = np.round(rng.normal(0.3, 1.0, 30), 1), np.round(rng.normal(0.0, 1.0, 20), 1)
    truth = np.concatenate([np.ones(x.size), np.zeros(y.size)])
    expected = sf.roc_auc(truth, np.concatenate([x, y]))
    assert sf.vargha_delaney_a(x, y) == pytest.approx(expected, abs=1e-15)


def test_swapping_gives_the_complement() -> None:
    x, y = [1.0, 4.0, 4.0], [2.0, 4.0]
    assert sf.vargha_delaney_a(y, x) == 1 - sf.vargha_delaney_a(x, y)
