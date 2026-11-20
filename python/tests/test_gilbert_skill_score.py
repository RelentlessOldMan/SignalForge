"""The Gilbert skill score (ADR 0439)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_takes_the_chance_hits_out_of_the_threat_score() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    tp = float(np.sum(t * d))
    chance = float(np.sum(t) * np.sum(d) / t.size)
    union = float(np.sum(np.maximum(t, d)))
    want = (tp - chance) / (union - chance)
    assert sf.gilbert_skill_score(t, d) == pytest.approx(want, rel=1e-14)


def test_is_at_most_the_jaccard_index() -> None:
    rng = np.random.default_rng(201)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = 1.0
        assert sf.gilbert_skill_score(t, d) <= sf.jaccard_index(t, d) + 1e-15


def test_rejects_equal_constant_records() -> None:
    with pytest.raises(ValueError):
        sf.gilbert_skill_score([1.0, 1.0], [1.0, 1.0])
