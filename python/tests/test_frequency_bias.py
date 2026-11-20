"""The frequency bias (ADR 0488)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_ratio_of_the_counts_and_swaps_to_its_reciprocal() -> None:
    rng = np.random.default_rng(251)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = 1.0
        d[0] = 1.0
        v = sf.frequency_bias(t, d)
        assert v == pytest.approx(float(np.sum(d)) / float(np.sum(t)), rel=1e-15)
        assert sf.frequency_bias(d, t) == pytest.approx(1.0 / v, rel=1e-14)


def test_rejects_truth_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.frequency_bias([0.0, 0.0], [1.0, 0.0])
