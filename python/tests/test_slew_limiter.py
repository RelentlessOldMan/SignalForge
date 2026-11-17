"""Slew-rate limiter (ADR 0242)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_steps_are_bounded() -> None:
    x = np.random.default_rng(17).standard_normal(500) * 3
    y = sf.slew_limiter(x, 0.2, 0.5)
    d = np.diff(np.concatenate([[0.0], y]))
    assert np.max(d) <= 0.2 + 1e-15
    assert np.min(d) >= -0.5 - 1e-15


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.slew_limiter(np.array([1 + 1j]), 1.0, 1.0)
