"""GCC-PHAT delay (conventions: GCC-PHAT delay; ADR 0191)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_delayed_noise_burst_is_found() -> None:
    s = np.random.default_rng(37).standard_normal(1200)
    r = sf.gcc_phat(s[100:1100], s[137:1137], 8000.0)
    assert r.lag == 37
    assert r.delay == pytest.approx(37 / 8000, abs=0.5 / 8000)


def test_max_delay_limits_the_search() -> None:
    s = np.random.default_rng(38).standard_normal(600)
    r = sf.gcc_phat(s[50:550], s[:500], 1.0, max_delay=20.0)
    assert abs(r.lag) <= 20


def test_complex_input_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.gcc_phat(np.array([1.0 + 1.0j]), np.array([1.0]), 1.0)
