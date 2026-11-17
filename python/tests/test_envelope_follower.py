"""Envelope follower (ADR 0238)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_tracks_a_tone_burst_amplitude() -> None:
    n = np.arange(6000)
    amp = np.where((n >= 1000) & (n < 3000), 2.0, 0.0)
    x = amp * np.sin(2 * np.pi * 0.05 * n)
    e = sf.envelope_follower(x, 0.5, 0.999)
    assert 1.95 < np.max(e[2000:3000]) <= 2.0
    assert np.min(e[2000:3000]) > 1.9
    assert e[5999] < 0.3
