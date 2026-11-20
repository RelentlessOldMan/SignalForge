"""The Gilbert-Wells coefficient (ADR 0463)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_at_most_ln_n() -> None:
    rng = np.random.default_rng(226)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0], d[0] = 1.0, 1.0
        v = sf.gilbert_wells_coefficient(t, d)
        assert v <= math.log(25) + 1e-15
        assert v == sf.gilbert_wells_coefficient(d, t)


def test_is_unchanged_when_every_item_is_repeated() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    twice = sf.gilbert_wells_coefficient(np.tile(t, 4), np.tile(d, 4))
    assert twice == sf.gilbert_wells_coefficient(t, d)


def test_rejects_records_that_share_no_one() -> None:
    with pytest.raises(ValueError):
        sf.gilbert_wells_coefficient([1.0, 0.0], [0.0, 1.0])
