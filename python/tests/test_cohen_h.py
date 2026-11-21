"""Cohen's h (ADR 0506)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_difference_of_the_arcsine_transforms_and_flips_with_the_truth() -> None:
    rng = np.random.default_rng(269)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        p1 = float(np.mean(t[d == 1]))
        p2 = float(np.mean(t[d == 0]))
        want = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
        v = sf.cohen_h(t, d)
        assert v == pytest.approx(want, abs=1e-12)
        assert sf.cohen_h(1 - t, d) == pytest.approx(-v, abs=1e-14)


def test_rejects_a_decision_with_no_zero() -> None:
    with pytest.raises(ValueError):
        sf.cohen_h([1.0, 0.0, 1.0], [1.0, 1.0, 1.0])
