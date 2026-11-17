"""Hampel filter (ADR 0235)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_removes_spikes_and_keeps_the_rest() -> None:
    rng = np.random.default_rng(12)
    x = rng.standard_normal(500)
    spikes = [50, 170, 333, 410]
    dirty = x.copy()
    dirty[spikes] += 40.0
    y = sf.hampel_filter(dirty, 11)
    assert np.all(np.abs(y[spikes]) < 5)
    kept = y == dirty
    assert kept.mean() > 0.95


def test_zero_threshold_is_the_median_filter_where_it_differs() -> None:
    x = np.array([3.0, -1.0, 4.0, 1.0, -5.0, 9.0, 2.0])
    assert np.array_equal(sf.hampel_filter(x, 3, 0.0), sf.median_filter(x, 3))
