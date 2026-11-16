"""Lateral energy fraction (conventions: Lateral energy fraction; ADR 0175)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_cosine_weighted_eight_gives_cos_squared() -> None:
    ir = np.random.default_rng(13).standard_normal(4800)
    ir[:240] = 0.0
    ir[0] = 3.0
    eight = 0.5 * ir
    eight[0] = 0.0
    expected = 0.25 * float(np.sum(ir[240:3840] ** 2)) / float(np.sum(ir[:3840] ** 2))
    assert sf.lateral_fraction(ir, eight, 48000.0) == pytest.approx(expected, rel=1e-12)


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.lateral_fraction(np.ones(4, complex), np.ones(4), 100.0)
