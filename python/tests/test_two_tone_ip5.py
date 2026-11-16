"""Two-tone fifth-order intermodulation and IP5 (conventions: Two-tone intermodulation;
ADR 0117)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 4096


def two_tones(a: float, k1: int, k2: int) -> np.ndarray:
    n = np.arange(N)
    return a * (np.cos(2 * np.pi * k1 * n / N) + np.cos(2 * np.pi * k2 * n / N))


@pytest.mark.parametrize("a", [0.1, 0.3])
@pytest.mark.parametrize("a5", [0.01, -0.5, 3.0])
def test_the_intercept_matches_the_expansion(a5: float, a: float) -> None:
    # y = x + a5 x^5 on equal tones: products (5/8) a5 A^5, tones A(1 + 6.25 a5 A^4)
    x = two_tones(a, 400, 433)
    r = sf.two_tone_ip5(x + a5 * x**5, N, 400, 433)
    pt = (a * (1 + 6.25 * a5 * a**4)) ** 2 / 2
    p5 = (5 / 8 * a5 * a**5) ** 2 / 2
    assert r.ip5_db == pytest.approx((50 * math.log10(pt) - 10 * math.log10(p5)) / 4, abs=1e-8)
    assert r.imd_dbc[0] == pytest.approx(r.imd_dbc[1], abs=1e-6)
    np.testing.assert_allclose(r.imd_frequencies, [334, 499])


def test_small_drive_tends_to_the_textbook_intercept() -> None:
    # A_IP5^4 = 8/(5|a5|); the tones' growth moves it by about 1.4e-3 dB at this drive
    x = two_tones(0.1, 400, 433)
    r = sf.two_tone_ip5(x + 0.2 * x**5, N, 400, 433)
    assert r.ip5_db == pytest.approx(10 * math.log10(math.sqrt(8 / (5 * 0.2)) / 2), abs=2e-3)


def test_a_cubic_has_no_fifth_order_products() -> None:
    x = two_tones(0.5, 400, 433)
    r = sf.two_tone_ip5(x + 0.1 * x**3, N, 400, 433)
    assert r.worst_imd_dbc < -200  # rounding only: a cubic makes no 3f1 - 2f2 line


def test_complex_envelope_quintic() -> None:
    # y = x + a5 |x|^4 x on A(e^{jw1 n} + e^{jw2 n}): products a5 A^5, tones A(1 + 10 a5 A^4)
    a, a5 = 0.3, 0.2
    n = np.arange(N)
    x = a * (np.exp(2j * np.pi * -300 * n / N) + np.exp(2j * np.pi * 200 * n / N))
    r = sf.two_tone_ip5(x + a5 * np.abs(x) ** 4 * x, N, -300, 200)
    pt = (a * (1 + 10 * a5 * a**4)) ** 2
    p5 = (a5 * a**5) ** 2
    np.testing.assert_allclose(r.imd_frequencies, [-1300, 1200])
    assert r.ip5_db == pytest.approx((5 * 10 * math.log10(pt) - 10 * math.log10(p5)) / 4, abs=1e-9)


def test_ip3_and_ip2_are_unchanged_by_the_shared_code() -> None:
    x = two_tones(1e-3, 400, 433)
    assert sf.two_tone_imd(x - 0.3 * x**3, N, 400, 433).ip3_db == pytest.approx(
        10 * math.log10(4 / (3 * 0.3) / 2), abs=2e-4
    )
    assert sf.two_tone_ip2(x + 0.2 * x**2, N, 400, 433).ip2_db == pytest.approx(
        10 * math.log10(1 / (2 * 0.2**2)), abs=1e-9
    )
