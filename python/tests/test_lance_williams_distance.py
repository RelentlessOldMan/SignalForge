"""The Lance-Williams distance (ADR 0476)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_less_the_dice_coefficient() -> None:
    rng = np.random.default_rng(239)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = 1.0
        v = sf.lance_williams_distance(t, d)
        tp = float(np.sum(t * d))
        assert v == pytest.approx(1 - 2 * tp / float(np.sum(t) + np.sum(d)), abs=1e-15)
        assert v == sf.lance_williams_distance(d, t)
        assert 0.0 <= v <= 1.0


def test_rejects_records_both_all_zero() -> None:
    with pytest.raises(ValueError):
        sf.lance_williams_distance([0.0, 0.0], [0.0, 0.0])
