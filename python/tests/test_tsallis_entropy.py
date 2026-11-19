"""Tsallis entropy (ADR 0356)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_falls_with_the_order() -> None:
    x = np.random.default_rng(63).standard_normal(2000)
    got = [sf.tsallis_entropy(x, q) for q in [0.0, 0.5, 1.0, 2.0, 5.0]]
    assert all(got[i] > got[i + 1] for i in range(len(got) - 1))


def test_is_continuous_at_one() -> None:
    x = np.random.default_rng(64).standard_normal(500)
    assert sf.tsallis_entropy(x, 1 - 1e-6) == pytest.approx(sf.tsallis_entropy(x, 1.0), abs=1e-5)


def test_rejects_a_negative_order() -> None:
    with pytest.raises(ValueError):
        sf.tsallis_entropy([0.0, 1.0], -1.0)
