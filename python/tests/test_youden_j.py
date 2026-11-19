"""Youden's J (ADR 0387)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_does_not_depend_on_how_common_the_positives_are() -> None:
    # Repeating the negatives changes the prevalence but not sensitivity or specificity.
    truth = [1.0, 1.0, 1.0, 0.0, 0.0]
    decision = [1.0, 0.0, 1.0, 1.0, 0.0]
    more = (truth + truth[3:] * 9, decision + decision[3:] * 9)
    assert sf.youden_j(*more) == pytest.approx(sf.youden_j(truth, decision), abs=1e-15)


def test_its_product_with_markedness_is_mcc_squared() -> None:
    rng = np.random.default_rng(116)
    truth = (rng.random(300) < 0.4).astype(float)
    decision = np.where(rng.random(300) < 0.75, truth, 1 - truth)
    product = sf.youden_j(truth, decision) * sf.youden_j(decision, truth)
    assert product == pytest.approx(sf.matthews_correlation(truth, decision) ** 2, rel=1e-12)


def test_rejects_a_missing_true_class() -> None:
    with pytest.raises(ValueError):
        sf.youden_j([1.0, 1.0], [1.0, 0.0])
