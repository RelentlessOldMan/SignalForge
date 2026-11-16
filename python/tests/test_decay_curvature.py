"""Decay curvature (conventions: Decay curvature; ADR 0182)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_it_is_the_ratio_of_t30_to_t20() -> None:
    rng = np.random.default_rng(32)
    h = rng.standard_normal(8000) * 0.998 ** np.arange(8000)
    t20 = sf.reverberation_time(h, 8000.0)
    t30 = sf.reverberation_time(h, 8000.0, stop_db=-35.0)
    assert sf.decay_curvature(h, 8000.0) == pytest.approx(100 * (t30 / t20 - 1), abs=1e-12)
