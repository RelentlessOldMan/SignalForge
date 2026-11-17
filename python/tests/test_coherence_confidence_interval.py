"""Coherence confidence interval (conventions: Coherence confidence interval; ADR 0202)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_interval_contains_the_estimate_and_narrows_with_segments() -> None:
    g2 = np.array([0.0, 0.1, 0.5, 0.9, 0.999])
    previous = np.full(g2.size, np.inf)
    for k in (2, 4, 16, 64, 1024):
        ci = sf.coherence_confidence_interval(g2, k)
        assert np.all(ci.lower <= g2) and np.all(ci.upper >= g2)
        assert np.all(ci.upper <= 1.0) and np.all(ci.lower >= 0.0)
        width = ci.upper - ci.lower
        assert np.all(width < previous)
        previous = width
