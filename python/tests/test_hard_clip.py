"""Hard clipper (ADR 0251)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_complex_keeps_phase_and_bounds_magnitude() -> None:
    rng = np.random.default_rng(25)
    x = rng.standard_normal(1000) + 1j * rng.standard_normal(1000)
    y = sf.hard_clip(x, 1.0)
    assert np.max(np.abs(y)) <= 1.0 + 1e-15
    inside = np.abs(x) <= 1.0
    assert np.array_equal(y[inside], x[inside])
    assert np.allclose(np.angle(y[~inside]), np.angle(x[~inside]), rtol=0, atol=1e-15)


def test_real_is_a_clamp() -> None:
    x = np.random.default_rng(26).standard_normal(500)
    assert np.array_equal(sf.hard_clip(x, 0.5), np.minimum(np.maximum(x, -0.5), 0.5))
