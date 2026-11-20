"""The Johnson coefficient (ADR 0470)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_twice_the_kulczynski_coefficient() -> None:
    rng = np.random.default_rng(233)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = d[0] = 1.0
        v = sf.johnson_coefficient(t, d)
        assert v == pytest.approx(2 * sf.kulczynski_coefficient(t, d), abs=1e-14)
        assert v == sf.johnson_coefficient(d, t)
        assert 0.0 <= v <= 2.0


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.johnson_coefficient([0.0, 0.0], [1.0, 0.0])
