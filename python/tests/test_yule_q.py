"""Yule's Q (ADR 0430)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_follows_from_the_odds_ratio() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    tp, fn = np.sum(t * d), np.sum(t * (1 - d))
    fp, tn = np.sum((1 - t) * d), np.sum((1 - t) * (1 - d))
    odds = tp * tn / (fn * fp)
    assert sf.yule_q(t, d) == pytest.approx((odds - 1) / (odds + 1), rel=1e-14)


def test_flipping_one_record_negates_it() -> None:
    rng = np.random.default_rng(189)
    t = (rng.random(30) < 0.5).astype(float)
    d = (rng.random(30) < 0.5).astype(float)
    assert sf.yule_q(t, 1 - d) == -sf.yule_q(t, d)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.yule_q([1.0, 1.0, 1.0], [1.0, 0.0, 1.0])
