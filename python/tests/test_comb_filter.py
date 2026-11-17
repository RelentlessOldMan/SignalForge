"""Comb filter (ADR 0237)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_feedforward_notches_its_frequency() -> None:
    d = 8
    n = np.arange(4000)
    tone = np.cos(2 * np.pi * n / (2 * d))
    y = sf.comb_filter(tone, d, 1.0)
    assert np.max(np.abs(y[d:])) < 1e-12


def test_feedback_matches_iir() -> None:
    x = np.random.default_rng(13).standard_normal(100)
    y = sf.comb_filter(x, 4, 0.7, feedback=True)
    want = np.zeros(100)
    for i in range(100):
        want[i] = x[i] + (0.7 * want[i - 4] if i >= 4 else 0.0)
    assert np.allclose(y, want, rtol=0, atol=1e-13)
