"""Energy separation (conventions: Energy separation; ADR 0189)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_slow_am_tone_follows_its_envelope() -> None:
    n = np.arange(400)
    env = 1 + 0.3 * np.cos(2 * np.pi * n / 400)
    r = sf.energy_separation(env * np.cos(0.5 * n), 1.0)
    assert np.allclose(r.amplitude, env[2:-2], rtol=1e-3)
    assert np.allclose(r.frequency, 0.5 / (2 * np.pi), rtol=1e-3)


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.energy_separation(np.ones(6, dtype=np.complex128), 1.0)
