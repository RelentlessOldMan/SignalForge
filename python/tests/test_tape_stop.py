"""Tape stop (ADR 0296)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_ramp_reads_back_the_running_sum_of_speeds() -> None:
    x = np.arange(5000, dtype=np.float64)
    y = sf.tape_stop(x, 1000, 2000)
    speeds = 1 - np.arange(1, 2000) / 2000
    assert y[1001:3000] == pytest.approx(1000 + np.cumsum(speeds), rel=0, abs=1e-9)
    assert np.all(np.diff(y[1000:3000]) > 0)
    assert np.all(y[3000:] == 0.0)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.tape_stop([1j], 0, 4)
