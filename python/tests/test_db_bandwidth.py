"""x dB bandwidth (conventions: Spectra, x dB bandwidth; ADR 0122)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("drop", [3.0, 6.0, 26.0])
def test_gaussian_psd(drop: float) -> None:
    f = np.linspace(-40, 40, 80001)
    sigma = 2.5
    p = 7 * np.exp(-((f - 0.75) ** 2) / (2 * sigma**2))
    r = sf.db_bandwidth(f, p, drop)
    # exp(-u^2 / (2 sigma^2)) = 10^(-drop/10) at u = sigma sqrt(drop ln 10 / 5)
    u = sigma * math.sqrt(drop * math.log(10) / 5)
    assert r.bandwidth == pytest.approx(2 * u, rel=1e-6)
    assert r.upper - 0.75 == pytest.approx(u, rel=1e-6)
    assert (r.lower + r.upper) / 2 == pytest.approx(0.75, abs=1e-9)
    assert r.peak_frequency == pytest.approx(0.75, abs=1e-12)


def test_rectangle_is_its_width_within_a_bin() -> None:
    f = np.arange(200, dtype=np.float64) * 0.25
    p = np.where((f >= 10) & (f <= 20), 1.0, 1e-6)
    r = sf.db_bandwidth(f, p, 20.0)
    width = 41 * 0.25  # bins 10 ... 20 Hz, each 0.25 Hz wide
    assert width - 0.25 <= r.bandwidth <= width + 0.25
    # the bin at 9.75 is at 1e-6, the one at 10 at 1: the 0.01 crossing lies between
    assert r.lower == pytest.approx(9.75 + 0.25 * (0.01 - 1e-6) / (1 - 1e-6), rel=1e-12)


def test_scaling_changes_only_the_peak() -> None:
    rng = np.random.default_rng(122)
    f = np.arange(101, dtype=np.float64)
    p = np.exp(-((f - 50) ** 2) / 200) * rng.uniform(0.9, 1.0, size=101)
    a = sf.db_bandwidth(f, p, 6.0)
    b = sf.db_bandwidth(f, 1e9 * p, 6.0)
    assert b.peak_psd == pytest.approx(1e9 * a.peak_psd, rel=1e-15)
    assert b.lower == pytest.approx(a.lower, rel=1e-12)
    assert b.upper == pytest.approx(a.upper, rel=1e-12)


def test_the_walk_stops_at_the_first_dip() -> None:
    f = np.arange(9, dtype=np.float64)
    p = np.array([0.0, 8.0, 1.0, 8.0, 10.0, 8.0, 1.0, 8.0, 0.0])
    r = sf.db_bandwidth(f, p, 3.0)
    assert 2 < r.lower < 3
    assert 5 < r.upper < 6
