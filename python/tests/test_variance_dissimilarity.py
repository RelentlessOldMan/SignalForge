"""The variance dissimilarity (ADR 0475)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_a_quarter_of_the_mismatch_share() -> None:
    rng = np.random.default_rng(238)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.variance_dissimilarity(t, d)
        assert v == pytest.approx(float(np.mean(t != d)) / 4, abs=1e-15)
        assert v == sf.variance_dissimilarity(d, t)
        assert 0.0 <= v <= 0.25


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.variance_dissimilarity([0.0, 1.0], [1.0])
