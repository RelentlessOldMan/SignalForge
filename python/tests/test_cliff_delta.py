"""Cliff's delta (ADR 0400)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_net_share_of_pairs() -> None:
    rng = np.random.default_rng(137)
    x, y = np.round(rng.normal(0.5, 1.0, 60), 1), np.round(rng.normal(0.0, 1.0, 45), 1)
    p, q = x[:, None], y[None, :]
    expected = np.mean(np.sign(p - q))
    assert sf.cliff_delta(x, y) == pytest.approx(expected, abs=1e-15)


def test_is_antisymmetric_and_rank_only() -> None:
    rng = np.random.default_rng(138)
    x, y = rng.normal(0.3, 1.0, 30), rng.normal(0.0, 1.0, 20)
    assert sf.cliff_delta(y, x) == -sf.cliff_delta(x, y)
    assert sf.cliff_delta(np.exp(x), np.exp(y)) == sf.cliff_delta(x, y)


def test_rejects_an_empty_sample() -> None:
    with pytest.raises(ValueError):
        sf.cliff_delta([], [1.0])
