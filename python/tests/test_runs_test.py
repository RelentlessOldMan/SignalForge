"""Runs test (ADR 0361)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_iid_noise_has_a_small_z() -> None:
    z = [sf.runs_test(np.random.default_rng(s).standard_normal(300)).z for s in range(300)]
    assert abs(np.mean(z)) < 0.2
    assert np.std(z) == pytest.approx(1.0, abs=0.15)


def test_a_trend_has_two_runs() -> None:
    assert sf.runs_test(np.arange(10.0)).runs == 2


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.runs_test([1.0, 1.0, 1.0])
