"""Interaural cross-correlation (conventions: Interaural cross-correlation; ADR 0174)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_delayed_scaled_copy_within_one_ms_gives_one() -> None:
    x = np.random.default_rng(11).standard_normal(2000)
    right = 0.3 * np.concatenate([np.zeros(20), x[:-20]])
    assert sf.iacc(x, right, 48000.0) == pytest.approx(1.0, abs=0.02)
    assert sf.iacc(x, right, 48000.0, max_lag=0.0002) < 0.2


def test_independent_noise_is_nearly_uncorrelated() -> None:
    rng = np.random.default_rng(12)
    assert sf.iacc(rng.standard_normal(20000), rng.standard_normal(20000), 48000.0) < 0.05
