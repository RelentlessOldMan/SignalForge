"""The pattern difference (ADR 0474)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_four_times_the_product_of_the_mismatch_shares() -> None:
    rng = np.random.default_rng(237)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.pattern_difference(t, d)
        want = 4 * float(np.mean((t == 1) & (d == 0))) * float(np.mean((t == 0) & (d == 1)))
        assert v == pytest.approx(want, abs=1e-15)
        assert v == sf.pattern_difference(d, t)
        assert 0.0 <= v <= 1.0


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.pattern_difference([0.0, 1.0], [1.0])
