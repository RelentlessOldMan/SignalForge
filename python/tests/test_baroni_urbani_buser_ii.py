"""The second Baroni-Urbani-Buser coefficient (ADR 0468)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_twice_the_first_less_one() -> None:
    rng = np.random.default_rng(231)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = 1.0
        v = sf.baroni_urbani_buser_ii(t, d)
        first = sf.baroni_urbani_buser_coefficient(t, d)
        assert v == pytest.approx(2 * first - 1, abs=1e-14)
        assert v == sf.baroni_urbani_buser_ii(d, t)
        assert -1.0 <= v <= 1.0


def test_is_minus_one_for_opposite_records() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
    assert sf.baroni_urbani_buser_ii(t, 1 - t) == -1.0


def test_rejects_records_both_all_zero() -> None:
    with pytest.raises(ValueError):
        sf.baroni_urbani_buser_ii([0.0, 0.0], [0.0, 0.0])
