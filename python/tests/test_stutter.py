"""Stutter (ADR 0299)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_slice_repeats_then_the_input_resumes() -> None:
    rng = np.random.default_rng(299)
    x = rng.standard_normal(1000)
    y = sf.stutter(x, 200, 50, 4)
    assert np.array_equal(y[:200], x[:200])
    for k in range(4):
        assert np.array_equal(y[200 + 50 * k : 250 + 50 * k], x[200:250])
    assert np.array_equal(y[400:], x[400:])


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.stutter([1j], 0, 1, 2)
