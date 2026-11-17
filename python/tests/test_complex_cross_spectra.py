"""Coherence, H1 and H2 of complex input (conventions: Complex coherence and transfer
functions; ADR 0197)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_complex_channel_and_shifted_frequencies() -> None:
    rng = np.random.default_rng(45)
    x = rng.standard_normal(2048) + 1j * rng.standard_normal(2048)
    h = np.array([0.7, 0.2j])
    y = np.convolve(x, h)[: x.size]
    r = sf.transfer_function(x, y, 8.0, nperseg=64)
    w = sf.welch_psd(x, 8.0, nperseg=64)
    assert np.array_equal(r.frequencies, w.frequencies)
    expected = h[0] + h[1] * np.exp(-2j * np.pi * r.frequencies / 8.0)
    assert np.allclose(r.response, expected, atol=0.05)
    c = sf.coherence(x, y, 8.0, nperseg=64).values
    h2 = sf.transfer_function_h2(x, y, 8.0, nperseg=64).response
    assert np.allclose(r.response / h2, c)


def test_real_input_matches_the_positive_half_of_the_complex_form() -> None:
    rng = np.random.default_rng(46)
    x = rng.standard_normal(512)
    y = np.convolve(x, [0.5, 0.3])[: x.size] + 0.1 * rng.standard_normal(x.size)
    real = sf.coherence(x, y, 1.0, nperseg=32)
    cplx = sf.coherence(x.astype(np.complex128), y, 1.0, nperseg=32)
    assert np.allclose(cplx.values[16:], real.values[:16])
