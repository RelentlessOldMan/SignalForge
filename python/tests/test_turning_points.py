"""Turning point test (ADR 0360)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_iid_noise_has_a_small_z() -> None:
    z = [sf.turning_points(np.random.default_rng(s).standard_normal(300)).z for s in range(300)]
    assert abs(np.mean(z)) < 0.2
    assert np.std(z) == pytest.approx(1.0, abs=0.15)


def test_a_smooth_record_has_few() -> None:
    x = np.sin(np.arange(1000) * 0.01)
    assert sf.turning_points(x).z < -20


def test_rejects_two_samples() -> None:
    with pytest.raises(ValueError):
        sf.turning_points([0.0, 1.0])
