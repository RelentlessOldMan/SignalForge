"""Noise-compensated decay (conventions: Noise-compensated decay; ADR 0183)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_compensation_straightens_a_noisy_decay() -> None:
    rng = np.random.default_rng(33)
    k = np.arange(16000)
    h = rng.standard_normal(16000) * (0.999**k + 0.003)
    plain = sf.schroeder_decay(h)
    fixed = sf.noise_compensated_decay(h, tail=0.25)
    line = 20 * np.log10(0.999) * 4000
    assert abs(fixed[4000] - line) < abs(plain[4000] - line)


def test_the_length_is_up_to_the_noise_window() -> None:
    assert sf.noise_compensated_decay(np.ones(10) * 0.5 ** np.arange(10), tail=0.2).shape == (8,)
