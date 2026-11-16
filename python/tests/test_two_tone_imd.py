"""Two-tone third-order intermodulation and IP3 (conventions: Two-tone intermodulation;
ADR 0107)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 4096


def two_tones(a: float, k1: int, k2: int) -> np.ndarray:
    n = np.arange(N)
    return a * (np.cos(2 * np.pi * k1 * n / N) + np.cos(2 * np.pi * k2 * n / N))


@pytest.mark.parametrize("a3", [0.02, -0.3, 1.5])
def test_small_drive_extrapolates_to_the_textbook_intercept(a3: float) -> None:
    # y = x + a3 x^3: the output intercept amplitude^2 is 4/(3|a3|) as the drive goes to 0
    x = two_tones(1e-3, 400, 433)
    r = sf.two_tone_imd(x + a3 * x**3, N, 400, 433)
    want = 10 * math.log10(4 / (3 * abs(a3)) / 2)
    assert r.ip3_db == pytest.approx(want, abs=2e-4)  # the finite drive compresses by ~4e-5 dB
    assert r.imd_dbc[0] == pytest.approx(r.imd_dbc[1], abs=1e-4)
    np.testing.assert_allclose(r.imd_frequencies, [367, 466])
    np.testing.assert_allclose(r.tone_frequencies, [400, 433], atol=1e-6)


def test_intercept_rises_one_db_per_db_of_imd_shift() -> None:
    # 1 dB more drive: tones +1 dB, products +3 dB, intercept unchanged
    x = two_tones(0.01, 300, 340)
    y = two_tones(0.01 * 10 ** (1 / 20), 300, 340)
    a, b = (
        sf.two_tone_imd(x + 0.1 * x**3, N, 300, 340),
        sf.two_tone_imd(y + 0.1 * y**3, N, 300, 340),
    )
    assert b.worst_imd_dbc - a.worst_imd_dbc == pytest.approx(2.0, abs=1e-3)
    assert b.ip3_db == pytest.approx(a.ip3_db, abs=1e-3)


def test_a_linear_device_has_no_products() -> None:
    r = sf.two_tone_imd(two_tones(1.0, 100, 150), N, 100, 150)
    assert np.all(r.imd_powers == 0)
    assert np.all(r.imd_dbc == -math.inf)
    assert r.worst_imd_dbc == -math.inf
    assert r.ip3_db == math.inf
    np.testing.assert_allclose(r.tone_powers, [0.5, 0.5], rtol=1e-12)


def test_complex_products_wrap() -> None:
    # f1 = -1800, f2 = 1900 of 4096: 2f2 - f1 = 5600 wraps to 1504, 2f1 - f2 = -5500 to -1404
    n = np.arange(N)
    x = 0.3 * (np.exp(-2j * np.pi * 1800 * n / N) + np.exp(2j * np.pi * 1900 * n / N))
    r = sf.two_tone_imd(x + 0.5 * np.abs(x) ** 2 * x, N, -1800, 1900)
    np.testing.assert_allclose(r.imd_frequencies, [-1404, 1504])
    np.testing.assert_allclose(r.imd_powers, [(0.5 * 0.3**3) ** 2] * 2, rtol=1e-9)


@pytest.mark.parametrize(
    ("f1", "f2"),
    [(433.0, 400.0), (400.0, math.nan), (math.inf, 433.0), (400.0, 2049.0), (400.0, 402.0)],
)
def test_bad_arguments(f1: float, f2: float) -> None:
    with pytest.raises(ValueError):
        sf.two_tone_imd(two_tones(1.0, 400, 433), N, f1, f2)
