"""Analytic signal (conventions: Analytic signal; ADR 0185)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("n", [1, 2, 7, 64, 99])
def test_the_real_part_is_the_input(n: int) -> None:
    x = np.random.default_rng(n).standard_normal(n)
    assert np.allclose(sf.analytic_signal(x).real, x, atol=1e-12)


def test_an_am_tone_has_its_envelope() -> None:
    n = np.arange(256)
    env = 1 + 0.5 * np.cos(2 * np.pi * 2 * n / 256)
    x = env * np.cos(2 * np.pi * 40 * n / 256)
    assert np.allclose(np.abs(sf.analytic_signal(x)), env, atol=1e-12)


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.analytic_signal(np.array([1.0 + 1.0j, 0.0]))
