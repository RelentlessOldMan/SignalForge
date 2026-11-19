"""von Neumann ratio (ADR 0362)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_iid_noise_is_near_two() -> None:
    x = np.random.default_rng(69).standard_normal(100_000)
    assert sf.von_neumann_ratio(x) == pytest.approx(2.0, abs=0.03)


def test_a_random_walk_is_small() -> None:
    x = np.cumsum(np.random.default_rng(70).standard_normal(2000))
    assert sf.von_neumann_ratio(x) < 0.1


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.von_neumann_ratio([1.0, 1.0])
