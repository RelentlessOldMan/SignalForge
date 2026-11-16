"""Decay time from a curve (conventions: Decay time from a curve; ADR 0184)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_reverberation_time_is_the_decay_time_of_the_schroeder_decay() -> None:
    rng = np.random.default_rng(34)
    h = rng.standard_normal(6000) * 0.998 ** np.arange(6000)
    d = sf.schroeder_decay(h)
    assert sf.reverberation_time(h, 8000.0) == sf.decay_time(d, 8000.0)
    assert sf.reverberation_time(h, 8000.0, start_db=0.0, stop_db=-10.0) == sf.decay_time(
        d, 8000.0, start_db=0.0, stop_db=-10.0
    )


def test_a_compensated_decay_can_be_fitted() -> None:
    rng = np.random.default_rng(35)
    h = rng.standard_normal(8000) * (0.999 ** np.arange(8000) + 0.002)
    t = sf.decay_time(sf.noise_compensated_decay(h, tail=0.25), 8000.0)
    assert np.isfinite(t) and t > 0
