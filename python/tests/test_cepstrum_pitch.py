"""Cepstrum pitch (conventions: Cepstrum pitch; ADR 0152)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

FS = 8000.0
PERIOD = 40


def pulse_train() -> np.ndarray:
    # 401 samples: not a whole number of periods, so no bin of the spectrum is 0.
    x = np.zeros(401)
    x[::PERIOD] = 1.0
    return np.convolve(x, [1.0, 0.6, 0.2])[:401]


def test_pulse_train_is_found_at_its_period() -> None:
    p = sf.cepstrum_pitch(pulse_train(), FS, 80.0, 400.0)
    assert round(p.quefrency) == PERIOD
    assert p.frequency == pytest.approx(FS / PERIOD, rel=2e-2)
    assert p.strength > 0


def test_scaling_leaves_it_unchanged() -> None:
    a = sf.cepstrum_pitch(pulse_train(), FS, 80.0, 400.0)
    b = sf.cepstrum_pitch(-5.0 * pulse_train(), FS, 80.0, 400.0)
    assert (b.frequency, b.quefrency, b.strength) == pytest.approx(
        (a.frequency, a.quefrency, a.strength), abs=1e-12
    )


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError, match="real"):
        sf.cepstrum_pitch(pulse_train() + 0j, FS, 80.0, 400.0)
