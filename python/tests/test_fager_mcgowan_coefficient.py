"""The Fager-McGowan coefficient (ADR 0438)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_fager_mcgowan_coefficient_less_a_correction() -> None:
    rng = np.random.default_rng(200)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        m = max(np.sum(t), np.sum(d))
        want = sf.ochiai_coefficient(t, d) - 1 / (2 * math.sqrt(m))
        assert sf.fager_mcgowan_coefficient(t, d) == pytest.approx(want, rel=1e-14, abs=1e-15)


def test_is_symmetric() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 1.0, 0.0]
    d = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0]
    assert sf.fager_mcgowan_coefficient(t, d) == sf.fager_mcgowan_coefficient(d, t)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.fager_mcgowan_coefficient([1.0, 0.0], [0.0, 0.0])
