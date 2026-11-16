"""Real cepstrum (conventions: Real cepstrum; ADR 0151)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

RNG = np.random.default_rng(151)
PERIOD = 40


def pulse_train() -> np.ndarray:
    # 401 samples: not a whole number of periods, so no bin of the spectrum is 0.
    x = np.zeros(401)
    x[::PERIOD] = 1.0
    return np.convolve(x, [1.0, 0.6, 0.2])[:401]


def test_pulse_train_peaks_at_its_period() -> None:
    c = sf.real_cepstrum(pulse_train())
    assert 20 + int(np.argmax(c[20:200])) == PERIOD


def test_result_is_real_and_even() -> None:
    c = sf.real_cepstrum(RNG.standard_normal(33), 64)
    assert c.dtype == np.float64 and c.shape == (64,)
    assert c[1:] == pytest.approx(c[1:][::-1], abs=1e-12)


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError, match="real"):
        sf.real_cepstrum([1.0 + 1j, 0.5])
