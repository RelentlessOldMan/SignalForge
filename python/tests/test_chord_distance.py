"""The chord distance of two binary records (ADR 0477)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_comes_from_the_ochiai_coefficient() -> None:
    rng = np.random.default_rng(240)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = d[0] = 1.0
        v = sf.chord_distance(t, d)
        o = sf.ochiai_coefficient(t, d)
        assert v == pytest.approx(math.sqrt(2 * (1 - o)), abs=1e-14)
        assert v == sf.chord_distance(d, t)
        assert 0.0 <= v <= math.sqrt(2)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.chord_distance([0.0, 0.0], [1.0, 0.0])
