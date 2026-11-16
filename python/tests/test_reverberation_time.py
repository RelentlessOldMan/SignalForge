"""Reverberation time (conventions: Reverberation time; ADR 0171)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_exponentially_decaying_noise_gives_its_design_time() -> None:
    fs, t60 = 8000.0, 0.5
    n = np.arange(int(2 * fs))
    envelope = 10 ** (-3 * n / (t60 * fs))
    ir = envelope * np.random.default_rng(8).standard_normal(n.shape[0])
    assert sf.reverberation_time(ir, fs) == pytest.approx(t60, rel=0.05)
    assert sf.reverberation_time(ir, fs, stop_db=-35.0) == pytest.approx(t60, rel=0.05)


def test_the_decay_starts_at_zero_and_never_rises() -> None:
    d = sf.schroeder_decay(np.random.default_rng(9).standard_normal(500))
    assert d[0] == 0.0
    assert np.all(np.diff(d) <= 0)
