"""Faith's coefficient (ADR 0456)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_of_russell_rao_and_simple_matching() -> None:
    rng = np.random.default_rng(219)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.faith_coefficient(t, d)
        want = (np.mean(t * d) + sf.simple_matching_coefficient(t, d)) / 2
        assert v == pytest.approx(want, rel=1e-15)
        assert v == sf.faith_coefficient(d, t)


def test_weighs_shared_ones_above_shared_zeros() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
    d = np.array([1.0, 1.0, 1.0, 1.0, 0.0])
    assert sf.faith_coefficient(t, d) > sf.faith_coefficient(1 - t, 1 - d)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.faith_coefficient([1.0, 0.0], [1.0])
