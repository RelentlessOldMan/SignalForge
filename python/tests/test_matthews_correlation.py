"""The Matthews correlation coefficient (ADR 0385)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_pearson_correlation_of_the_two_records() -> None:
    rng = np.random.default_rng(114)
    truth = (rng.random(500) < 0.3).astype(float)
    decision = np.where(rng.random(500) < 0.8, truth, 1 - truth)
    expected = sf.pearson_correlation(truth, decision)
    assert sf.matthews_correlation(truth, decision) == pytest.approx(expected, abs=1e-12)


def test_is_symmetric() -> None:
    truth = [1.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    decision = [1.0, 0.0, 0.0, 1.0, 0.0, 1.0]
    assert sf.matthews_correlation(truth, decision) == sf.matthews_correlation(decision, truth)


def test_rejects_a_missing_class() -> None:
    with pytest.raises(ValueError):
        sf.matthews_correlation([1.0, 0.0], [1.0, 1.0])
