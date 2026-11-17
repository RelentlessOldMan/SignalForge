"""LPC cepstrum (conventions: LPC cepstrum; ADR 0207)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_series_gives_the_model_log_spectrum() -> None:
    a = np.array([1.0, -1.2, 0.6, -0.1])
    error = 0.7
    c = sf.lpc_cepstrum(a, error, 200)
    w = np.linspace(0, np.pi, 33)
    model = np.log(error / np.abs(np.polyval(a[::-1], np.exp(1j * w)) / np.exp(1j * w * 3)) ** 2)
    series = 2 * np.real(np.exp(-1j * np.outer(w, np.arange(200))) @ c)
    assert np.allclose(series, model, atol=1e-10)


def test_real_coefficients_give_a_real_array() -> None:
    assert sf.lpc_cepstrum([1.0, 0.5], 1.0, 4).dtype == np.float64
    assert np.iscomplexobj(sf.lpc_cepstrum([1.0, 0.5j], 1.0, 4))
