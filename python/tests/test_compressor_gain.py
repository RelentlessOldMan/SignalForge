"""Compressor gain computer (ADR 0254)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_curve_and_slope_are_continuous() -> None:
    x = np.linspace(-60, 0, 60001)
    g = sf.compressor_gain(x, -24.0, 5.0, knee_db=10.0)
    assert np.max(np.abs(np.diff(g))) < 1e-3
    slope = np.diff(g) / np.diff(x)
    assert np.max(np.abs(np.diff(slope))) < 1e-3
    assert np.all(g <= 0)


def test_far_above_threshold_follows_the_ratio() -> None:
    g = sf.compressor_gain([0.0], -40.0, 4.0, knee_db=6.0)
    assert g[0] == pytest.approx(-30.0, abs=1e-12)
