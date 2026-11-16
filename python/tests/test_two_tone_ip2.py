"""Two-tone second-order intermodulation and IP2 (conventions: Two-tone intermodulation;
ADR 0110)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 4096


def two_tones(a: float, k1: int, k2: int) -> np.ndarray:
    n = np.arange(N)
    return a * (np.cos(2 * np.pi * k1 * n / N) + np.cos(2 * np.pi * k2 * n / N))


@pytest.mark.parametrize("a2", [0.01, -0.5, 3.0])
def test_small_drive_extrapolates_to_the_textbook_intercept(a2: float) -> None:
    # y = x + a2 x^2: the products are exactly a2 A^2 at any drive, so IP2 is A_IP2 = 1/|a2|
    x = two_tones(1e-3, 400, 433)
    r = sf.two_tone_ip2(x + a2 * x**2, N, 400, 433)
    assert r.ip2_db == pytest.approx(10 * math.log10(1 / (2 * a2**2)), abs=1e-9)
    assert r.imd_dbc[0] == pytest.approx(r.imd_dbc[1], abs=1e-9)
    np.testing.assert_allclose(r.imd_frequencies, [33, 833])


def test_the_intercept_does_not_move_with_drive() -> None:
    # slope 2 against slope 1: every 1 dB of drive moves the products 2 dB and IP2 not at all
    got = []
    for a in (1e-3, 1e-2, 1e-1):
        x = two_tones(a, 400, 433)
        got.append(sf.two_tone_ip2(x + 0.2 * x**2, N, 400, 433).ip2_db)
    np.testing.assert_allclose(got, got[0], atol=1e-9)


def test_odd_order_only_has_no_second_order_products() -> None:
    x = two_tones(0.5, 400, 433)
    r = sf.two_tone_ip2(x + 0.1 * x**3, N, 400, 433)
    assert r.worst_imd_dbc < -200  # rounding only: a cubic makes no sum or difference line
    assert r.ip2_db > 50


def test_ip3_is_unchanged_by_the_shared_code() -> None:
    x = two_tones(1e-3, 400, 433)
    r = sf.two_tone_imd(x - 0.3 * x**3, N, 400, 433)
    assert r.ip3_db == pytest.approx(10 * math.log10(4 / (3 * 0.3) / 2), abs=2e-4)
