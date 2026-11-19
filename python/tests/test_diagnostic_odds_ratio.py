"""The diagnostic odds ratio (ADR 0390)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_ratio_of_the_likelihood_ratios() -> None:
    rng = np.random.default_rng(120)
    truth = (rng.random(400) < 0.4).astype(float)
    decision = np.where(rng.random(400) < 0.75, truth, 1 - truth)
    t, d = truth == 1, decision == 1
    sensitivity = np.sum(t & d) / np.sum(t)
    specificity = np.sum(~t & ~d) / np.sum(~t)
    expected = (sensitivity / (1 - specificity)) / ((1 - sensitivity) / specificity)
    assert sf.diagnostic_odds_ratio(truth, decision) == pytest.approx(expected, rel=1e-13)


def test_does_not_depend_on_how_common_the_positives_are() -> None:
    truth = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    decision = [1.0, 1.0, 0.0, 1.0, 0.0, 0.0]
    more = (truth + truth[3:] * 4, decision + decision[3:] * 4)
    assert sf.diagnostic_odds_ratio(*more) == sf.diagnostic_odds_ratio(truth, decision)


def test_rejects_no_false_negative() -> None:
    with pytest.raises(ValueError):
        sf.diagnostic_odds_ratio([1.0, 0.0, 0.0], [1.0, 1.0, 0.0])
