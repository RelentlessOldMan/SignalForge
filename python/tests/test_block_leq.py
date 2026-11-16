"""Short Leq series and sound exposure (conventions: Short Leq series and sound exposure;
ADR 0170)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_block_means_average_to_the_overall_leq() -> None:
    x = np.random.default_rng(5).standard_normal(48000)
    blocks = sf.block_leq(x, 48000.0, 0.1)
    assert blocks.shape == (10,)
    assert blocks.mean() == pytest.approx(sf.power_stats(x).mean_power, rel=1e-12)


def test_exposure_is_leq_times_duration() -> None:
    x = np.random.default_rng(6).standard_normal(12000)
    assert sf.sound_exposure(x, 8000.0) == pytest.approx(
        sf.power_stats(x).mean_power * 1.5, rel=1e-12
    )
