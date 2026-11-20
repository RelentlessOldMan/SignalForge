"""The Baroni-Urbani-Buser coefficient (ADR 0433)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_never_below_the_jaccard_index() -> None:
    rng = np.random.default_rng(194)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = 1.0
        assert sf.baroni_urbani_buser_coefficient(t, d) >= sf.jaccard_index(t, d) - 1e-15


def test_is_the_jaccard_index_without_shared_zeros() -> None:
    t = np.array([1.0, 1.0, 0.0, 1.0, 0.0, 1.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0])
    assert sf.baroni_urbani_buser_coefficient(t, d) == pytest.approx(
        sf.jaccard_index(t, d), rel=1e-15
    )


def test_rejects_records_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.baroni_urbani_buser_coefficient([0.0, 0.0], [0.0, 0.0])
