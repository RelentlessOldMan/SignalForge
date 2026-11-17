"""Magnitude-squared coherence (conventions: Coherence; ADR 0192)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_filtered_noise_is_coherent_and_independent_noise_is_not() -> None:
    rng = np.random.default_rng(39)
    x = rng.standard_normal(8192)
    y = np.convolve(x, [0.5, 0.3, 0.1])[: x.size]
    c = sf.coherence(x, y, 1.0, nperseg=256)
    assert np.all(c.values > 0.98)
    z = rng.standard_normal(8192)
    assert np.mean(sf.coherence(x, z, 1.0, nperseg=256).values) < 0.05


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.coherence(np.ones(8, dtype=np.complex128), np.ones(8), 1.0)
