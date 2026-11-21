"""The standard error of Cohen's h (ADR 0507)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_depends_only_on_the_group_sizes() -> None:
    rng = np.random.default_rng(270)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        n1 = int(np.count_nonzero(d == 1))
        want = math.sqrt(1 / n1 + 1 / (25 - n1))
        v = sf.cohen_h_standard_error(t, d)
        assert v == pytest.approx(want, rel=1e-15)
        assert sf.cohen_h_standard_error(1 - t, d) == v


def test_rejects_a_decision_with_no_zero() -> None:
    with pytest.raises(ValueError):
        sf.cohen_h_standard_error([1.0, 0.0, 1.0], [1.0, 1.0, 1.0])
