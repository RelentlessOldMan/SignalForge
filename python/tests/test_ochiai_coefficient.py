"""The Ochiai coefficient (ADR 0429)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_cosine_of_the_records() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    cos = float(t @ d / (np.linalg.norm(t) * np.linalg.norm(d)))
    assert sf.ochiai_coefficient(t, d) == pytest.approx(cos, rel=1e-15)


def test_lies_between_dice_and_kulczynski() -> None:
    rng = np.random.default_rng(188)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        o = sf.ochiai_coefficient(t, d)
        assert sf.tversky_index(t, d, 0.5, 0.5) - 1e-15 <= o
        assert o <= sf.kulczynski_coefficient(t, d) + 1e-15


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.ochiai_coefficient([1.0, 0.0], [0.0, 0.0])
