"""Bark scale (conventions: Bark scale; ADR 0163)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_round_trip_and_increasing_over_the_audio_band() -> None:
    f = np.concatenate(([0.0], np.geomspace(1.0, 1e6, 400)))
    z = np.asarray(sf.hz_to_bark(f))
    assert np.all(np.diff(z) > 0)
    assert np.asarray(sf.bark_to_hz(z)) == pytest.approx(f, rel=1e-11, abs=1e-9)


def test_continuous_at_both_branch_edges() -> None:
    for edge in (1960 * 2.53 / 24.28, 1960 * 20.63 / 6.18):
        lo, hi = sf.hz_to_bark(edge * (1 - 1e-12)), sf.hz_to_bark(edge * (1 + 1e-12))
        assert hi - lo == pytest.approx(0.0, abs=1e-9)


def test_zero_round_trips_to_exactly_zero() -> None:
    assert sf.bark_to_hz(sf.hz_to_bark(0.0)) == 0.0
