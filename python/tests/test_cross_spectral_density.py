"""Cross-spectral density (conventions: Cross-spectral density; ADR 0194)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_same_signal_is_the_welch_psd() -> None:
    x = np.random.default_rng(41).standard_normal(1000)
    p = sf.cross_spectral_density(x, x, 50.0, nperseg=128, detrend="linear")
    w = sf.welch_psd(x, 50.0, nperseg=128, detrend="linear")
    assert np.allclose(p.csd.real, w.psd)
    assert np.allclose(p.csd.imag, 0.0)


def test_h1_is_csd_over_psd() -> None:
    rng = np.random.default_rng(42)
    x = rng.standard_normal(2048)
    y = np.convolve(x, [0.4, -0.2])[: x.size]
    p = sf.cross_spectral_density(x, y, 1.0, nperseg=128)
    w = sf.welch_psd(x, 1.0, nperseg=128)
    t = sf.transfer_function(x, y, 1.0, nperseg=128)
    assert np.allclose(p.csd / w.psd, t.response)


def test_complex_same_signal_is_the_complex_welch_psd() -> None:
    rng = np.random.default_rng(44)
    x = rng.standard_normal(600) + 1j * rng.standard_normal(600)
    p = sf.cross_spectral_density(x, x, 10.0, nperseg=64)
    w = sf.welch_psd(x, 10.0, nperseg=64)
    assert np.allclose(p.csd.real, w.psd)
    assert np.allclose(p.frequencies, w.frequencies)


def test_one_sided_complex_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.cross_spectral_density(np.ones(4, dtype=np.complex128), np.ones(4), 1.0, one_sided=True)
