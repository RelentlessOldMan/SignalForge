"""The Kulczynski coefficient (ADR 0428)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_of_recall_and_precision() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    tp = float(np.sum(t * d))
    want = (tp / np.sum(t) + tp / np.sum(d)) / 2
    assert sf.kulczynski_coefficient(t, d) == pytest.approx(want, rel=1e-15)


def test_is_at_least_the_dice_coefficient() -> None:
    rng = np.random.default_rng(187)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        assert sf.kulczynski_coefficient(t, d) >= sf.tversky_index(t, d, 0.5, 0.5) - 1e-15


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.kulczynski_coefficient([1.0, 0.0], [0.0, 0.0])
