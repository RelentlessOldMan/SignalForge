"""Coherence significance threshold (conventions: Coherence threshold; ADR 0199)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_false_alarm_rate_on_independent_noise() -> None:
    rng = np.random.default_rng(48)
    k = 8
    t = sf.coherence_threshold(k, 0.1)
    hits = 0
    for _ in range(200):
        x = rng.standard_normal(64 * k)
        y = rng.standard_normal(64 * k)
        c = sf.coherence(x, y, 1.0, nperseg=64, noverlap=0, window="rectangular").values[1:-1]
        hits += int(np.sum(c > t))
    assert abs(hits / (200 * 31) - 0.1) < 0.015  # 6200 bins, sd about 0.004
