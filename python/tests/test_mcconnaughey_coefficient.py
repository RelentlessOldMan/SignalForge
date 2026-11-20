"""The McConnaughey coefficient (ADR 0436)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_twice_kulczynski_less_one() -> None:
    rng = np.random.default_rng(197)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        want = 2 * sf.kulczynski_coefficient(t, d) - 1
        assert sf.mcconnaughey_coefficient(t, d) == pytest.approx(want, rel=1e-14, abs=1e-15)


def test_is_minus_one_with_no_shared_one() -> None:
    assert sf.mcconnaughey_coefficient([1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]) == -1.0


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.mcconnaughey_coefficient([1.0, 0.0], [0.0, 0.0])
