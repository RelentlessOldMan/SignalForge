"""The Austin-Colwell coefficient (ADR 0448)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_arcsine_of_the_root_of_simple_matching() -> None:
    rng = np.random.default_rng(211)
    for _ in range(20):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.austin_colwell_coefficient(t, d)
        p = float(np.mean(t == d))
        assert math.sin(math.pi * v / 2) ** 2 == pytest.approx(p, rel=1e-13, abs=1e-15)


def test_flipping_a_record_gives_one_minus_the_value() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    v = sf.austin_colwell_coefficient(t, d)
    assert sf.austin_colwell_coefficient(t, 1 - d) == pytest.approx(1 - v, rel=1e-14)
    assert sf.austin_colwell_coefficient(d, t) == v


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.austin_colwell_coefficient([0.0, 1.0], [0.0])
