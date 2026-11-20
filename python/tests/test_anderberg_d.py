"""Anderberg's D (ADR 0446)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_lies_between_zero_and_a_half_and_is_symmetric() -> None:
    rng = np.random.default_rng(209)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.anderberg_d(t, d)
        assert 0.0 <= v <= 0.5
        assert v == sf.anderberg_d(d, t)


def test_is_unchanged_when_a_record_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    assert sf.anderberg_d(t, 1 - d) == sf.anderberg_d(t, d)
    assert sf.anderberg_d(1 - t, d) == sf.anderberg_d(t, d)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.anderberg_d([0.0, 1.0], [0.0])
