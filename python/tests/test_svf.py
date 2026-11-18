"""State-variable filter (ADR 0279)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_outputs_sum_to_the_input() -> None:
    rng = np.random.default_rng(48)
    x = rng.standard_normal(300)
    q = 3.0
    lo = sf.svf(x, 500.0, q, 8000.0)
    bp = sf.svf(x, 500.0, q, 8000.0, output="bandpass")
    hp = sf.svf(x, 500.0, q, 8000.0, output="highpass")
    no = sf.svf(x, 500.0, q, 8000.0, output="notch")
    assert np.allclose(lo + bp / q + hp, x, rtol=0, atol=1e-12)
    assert np.allclose(no, lo + hp, rtol=0, atol=1e-12)


def test_gains_at_the_cutoff() -> None:
    fs, fc, q = 8000.0, 1000.0, 4.0
    n = np.arange(8000)
    x = np.sin(2 * np.pi * fc * n / fs)
    tail = slice(6000, None)
    bp = np.real(sf.svf(x, fc, q, fs, output="bandpass"))
    no = np.real(sf.svf(x, fc, q, fs, output="notch"))
    assert np.max(np.abs(bp[tail])) == pytest.approx(q, rel=1e-6)
    assert np.max(np.abs(no[tail])) < 1e-6


def test_rejects_cutoff_at_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.svf([1.0], 4.0, 1.0, 8.0)
