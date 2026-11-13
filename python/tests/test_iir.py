"""Butterworth design, section responses and the streaming IIR filter (conventions: IIR filters)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import (
    IirFilter,
    bessel_bandpass,
    bessel_bandstop,
    bessel_highpass,
    bessel_lowpass,
    butterworth_bandpass,
    butterworth_bandstop,
    butterworth_highpass,
    butterworth_lowpass,
    chebyshev1_bandpass,
    chebyshev1_bandstop,
    chebyshev1_highpass,
    chebyshev1_lowpass,
    chebyshev2_bandpass,
    chebyshev2_bandstop,
    chebyshev2_highpass,
    chebyshev2_lowpass,
    elliptic_bandpass,
    elliptic_bandstop,
    elliptic_highpass,
    elliptic_lowpass,
    sos_response,
    zero_phase_filter,
)

DESIGNS = [butterworth_lowpass, butterworth_highpass]


@pytest.mark.parametrize("design", DESIGNS)
@pytest.mark.parametrize("order", [1, 2, 3, 6, 9, 16])
@pytest.mark.parametrize("cutoff", [0.003, 0.1, 0.37, 0.499])
def test_butterworth_magnitude_has_the_closed_form(design: Any, order: int, cutoff: float) -> None:
    sos = design(order, cutoff * 48000, 48000.0)
    assert sos.shape == ((order + 1) // 2, 6)
    assert np.all(sos[:, 3] == 1)
    f = np.linspace(-0.4999, 0.4999, 301) * 48000
    k = math.tan(math.pi * cutoff)
    t = np.abs(np.tan(np.pi * f / 48000))
    with np.errstate(divide="ignore", over="ignore"):
        r = k / t if design is butterworth_highpass else t / k
        expected = 1 / (1 + r ** (2 * order))
    got = np.abs(sos_response(sos, f, 48000.0)) ** 2
    assert np.allclose(got, expected, rtol=1e-9, atol=1e-12)
    assert abs(sos_response(sos, [cutoff * 48000], 48000.0)[0]) ** 2 == pytest.approx(0.5, rel=1e-9)


@pytest.mark.parametrize("design", DESIGNS)
@pytest.mark.parametrize("order", [1, 4, 7])
def test_butterworth_is_stable_with_unit_gain_sections(design: Any, order: int) -> None:
    sos = design(order, 1500.0, 8000.0)
    ref = 4000.0 if design is butterworth_highpass else 0.0
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
        assert abs(sos_response(row[None, :], [ref], 8000.0)[0]) == pytest.approx(1, abs=1e-14)
    a2 = sos[order % 2 :, 5]  # pole radius squared rises with Q: the sharpest section is last
    assert np.all(np.diff(a2) >= 0)


def test_impulse_response_spectrum_matches_sos_response() -> None:
    sos = butterworth_lowpass(5, 900.0, 8000.0)
    impulse = np.zeros(4096)
    impulse[0] = 1
    h = IirFilter(sos).process(impulse)
    k = np.arange(0, 2048, 37)
    assert np.allclose(np.fft.fft(h)[k], sos_response(sos, k * 8000.0 / 4096, 8000.0), atol=1e-12)


@pytest.mark.parametrize("dtype", [np.float64, np.complex128])
def test_chunks_concatenate_to_one_pass(dtype: Any) -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(301).astype(dtype)
    if dtype is np.complex128:
        x = x + 1j * rng.standard_normal(301)
    f = IirFilter(butterworth_highpass(6, 0.2, 1.0))
    whole = f.process(x)
    f.reset()
    parts = [f.process(x[i:j]) for i, j in [(0, 1), (1, 1), (1, 120), (120, 301)]]
    assert np.array_equal(np.concatenate(parts), whole)
    assert whole.dtype == dtype


def test_real_or_complex_until_reset() -> None:
    f = IirFilter([[1, 0, 0, 1, -0.5, 0]])
    assert f.process([]).dtype == np.float64
    f.process([1.0])
    with pytest.raises(ValueError, match="real"):
        f.process([1j])
    f.reset()
    assert f.process([1j])[0] == 1j
    with pytest.raises(ValueError, match="complex"):
        f.process([1.0])
    assert f.process(np.zeros(0, dtype=complex)).dtype == np.complex128
    with pytest.raises(ValueError):
        f.process(np.ones((2, 2)))


def test_sections_are_a_normalized_copy() -> None:
    sos = np.array([[2.0, 4.0, 2.0, 2.0, 1.0, 0.5]])
    f = IirFilter(sos)
    sos[0, 0] = 99
    s = f.sections
    assert np.array_equal(s, [[1.0, 2.0, 1.0, 1.0, 0.5, 0.25]])
    s[0, 0] = 99
    assert f.sections[0, 0] == 1


@pytest.mark.parametrize(
    "sos",
    [
        [],
        [[1, 0, 0, 1, 0]],
        [1, 0, 0, 1, 0, 0],
        [[1, 0, 0, 0, 0, 0]],
        [[1, 0, 0, 1, math.nan, 0]],
        [[1, 0, 0, 1, math.inf, 0]],
        [[1j, 0, 0, 1, 0, 0]],
    ],
)
def test_bad_sections_raise(sos: Any) -> None:
    with pytest.raises(ValueError):
        IirFilter(sos)
    with pytest.raises(ValueError):
        sos_response(sos, [0.0], 1.0)


@pytest.mark.parametrize("design", DESIGNS)
@pytest.mark.parametrize(
    ("order", "cutoff", "rate"),
    [
        (0, 1.0, 8.0),
        (2.0, 1.0, 8.0),
        (True, 1.0, 8.0),
        (2, math.nan, 8.0),
        (2, -1.0, 8.0),
        (2, 4.0, 8.0),
        (2, 1.0, math.inf),
        (2, 1.0, -8.0),
    ],
)
def test_bad_design_arguments_raise(design: Any, order: Any, cutoff: float, rate: float) -> None:
    with pytest.raises(ValueError):
        design(order, cutoff, rate)


def test_sos_response_rejects_bad_frequencies() -> None:
    with pytest.raises(ValueError):
        sos_response([[1, 0, 0, 1, 0, 0]], [math.nan], 1.0)
    with pytest.raises(ValueError):
        sos_response([[1, 0, 0, 1, 0, 0]], [[0.0]], 1.0)
    with pytest.raises(ValueError):
        sos_response([[1, 0, 0, 1, 0, 0]], [0.0], 0.0)


@pytest.mark.parametrize("stop", [False, True])
@pytest.mark.parametrize("order", [1, 2, 3, 6, 9])
@pytest.mark.parametrize("band", [(0.001, 0.002), (0.1, 0.11), (0.05, 0.45), (0.3, 0.4999)])
def test_butterworth_band_magnitude_has_the_closed_form(
    stop: bool, order: int, band: tuple[float, float]
) -> None:
    design = butterworth_bandstop if stop else butterworth_bandpass
    sos = design(order, band[0] * 1000, band[1] * 1000, 1000.0)
    assert sos.shape == (order, 6)
    assert np.all(sos[:, 3] == 1)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    lo, hi = math.tan(math.pi * band[0]), math.tan(math.pi * band[1])
    f = np.linspace(-0.4999, 0.4999, 301) * 1000
    t = np.abs(np.tan(np.pi * f / 1000))
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        x = (t * t - lo * hi) / ((hi - lo) * t)
        x2 = x ** (2 * order)
        expected = np.where(np.isinf(x2), 1.0, x2 / (1 + x2)) if stop else 1 / (1 + x2)
    got = np.abs(sos_response(sos, f, 1000.0)) ** 2
    assert np.allclose(got, expected, rtol=1e-9, atol=1e-11)
    edges = np.abs(sos_response(sos, [band[0] * 1000, band[1] * 1000], 1000.0)) ** 2
    assert edges == pytest.approx([0.5, 0.5], rel=1e-9)


def test_butterworth_bandpass_passes_its_center_and_bandstop_nulls_it() -> None:
    f0 = 8000 / math.pi * math.atan(math.sqrt(math.tan(math.pi / 8) * math.tan(math.pi / 4)))
    bp = butterworth_bandpass(4, 1000.0, 2000.0, 8000.0)
    bs = butterworth_bandstop(4, 1000.0, 2000.0, 8000.0)
    assert abs(sos_response(bp, [f0], 8000.0)[0]) == pytest.approx(1.0, abs=1e-12)
    assert abs(sos_response(bs, [f0], 8000.0)[0]) < 1e-12
    assert abs(sos_response(bs, [0.0, 4000.0], 8000.0)) == pytest.approx([1.0, 1.0], abs=1e-12)
    n = np.arange(4000)
    x = np.cos(2 * np.pi * f0 * n / 8000)
    y = IirFilter(bp).process(x)
    assert np.max(np.abs(y[3000:] - x[3000:])) < 1e-9  # unit gain, zero phase at the center


@pytest.mark.parametrize("design", [butterworth_bandpass, butterworth_bandstop])
@pytest.mark.parametrize(
    "args",
    [
        (0, 1.0, 2.0, 8.0),
        (2, 2.0, 1.0, 8.0),
        (2, 1.0, 1.0, 8.0),
        (2, 0.0, 1.0, 8.0),
        (2, 1.0, 4.0, 8.0),
        (2, 1.0, math.nan, 8.0),
        (2, 1.0, 2.0, 0.0),
        (2.0, 1.0, 2.0, 8.0),
    ],
)
def test_butterworth_band_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize("f", [200.0, 900.0, 1300.0])
def test_zero_phase_filter_scales_a_tone_by_h_squared_without_delay(f: float) -> None:
    sos = butterworth_lowpass(5, 1000.0, 8000.0)
    n = np.arange(4000)
    x = np.cos(2 * np.pi * f * n / 8000 + 0.3)
    y = zero_phase_filter(sos, x)
    h2 = abs(sos_response(sos, [f], 8000.0)[0]) ** 2
    assert np.max(np.abs(y[1000:3000] - h2 * x[1000:3000])) < 1e-9


def test_zero_phase_filter_keeps_the_kind_and_is_linear() -> None:
    sos = butterworth_bandpass(2, 0.1, 0.2, 1.0)
    rng = np.random.default_rng(3)
    re, im = rng.standard_normal(200), rng.standard_normal(200)
    yr, yi = zero_phase_filter(sos, re, pad=10), zero_phase_filter(sos, im, pad=10)
    z = zero_phase_filter(sos, re + 1j * im, pad=10)
    assert yr.dtype == np.float64 and z.dtype == np.complex128
    assert np.allclose(z, yr + 1j * yi, rtol=0, atol=1e-12)
    assert np.allclose(zero_phase_filter(sos, np.full(50, 2.0)), 0.0, atol=1e-12)


@pytest.mark.parametrize(
    ("sos", "x", "pad"),
    [
        ([[1, 0, 0, 1, -1, 0]], np.ones(8), 0),
        ([[1, 0, 0, 1, 0, 0]], np.ones(8), 8),
        ([[1, 0, 0, 1, 0, 0]], np.ones(8), -1),
        ([[1, 0, 0, 1, 0, 0]], np.ones(8), 1.0),
        ([[1, 0, 0, 1, 0, 0]], np.ones(8), True),
        ([[1, 0, 0, 1, 0, 0]], [1.0, math.nan, 1.0, 1.0], 0),
        ([[1, 0, 0, 1, 0, 0]], [1.0, complex(1, math.inf), 1.0, 1.0], 0),
        ([[2, 0, 0, 2, -2, 0]], np.ones(8), 0),
        ([[1, 0, 0, 1, 0, 0]], np.ones(9), None),
        ([[1, 0, 0, 1, 0, 0]], np.ones((2, 20)), 0),
        ([[1, 0, 0, 1, 0, 0]], [], 0),
    ],
)
def test_zero_phase_filter_rejects_bad_arguments(sos: Any, x: Any, pad: Any) -> None:
    with pytest.raises(ValueError):
        zero_phase_filter(sos, x, pad)


def _cheb_t(n: int, x: NDArray[np.float64]) -> NDArray[np.float64]:
    with np.errstate(invalid="ignore", over="ignore"):
        inside = np.cos(n * np.arccos(np.clip(x, -1, 1)))
        outside = np.sign(x) ** n * np.cosh(n * np.arccosh(np.maximum(np.abs(x), 1)))
    return np.where(np.abs(x) <= 1, inside, outside)


@pytest.mark.parametrize("high", [False, True])
@pytest.mark.parametrize("order", [1, 2, 3, 6, 9])
@pytest.mark.parametrize(("ripple", "cutoff"), [(0.1, 0.01), (1.0, 0.2), (3.0, 0.49), (0.5, 0.25)])
def test_chebyshev1_magnitude_has_the_closed_form(
    high: bool, order: int, ripple: float, cutoff: float
) -> None:
    design = chebyshev1_highpass if high else chebyshev1_lowpass
    sos = design(order, ripple, cutoff * 1000, 1000.0)
    assert sos.shape == ((order + 1) // 2, 6)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    eps2 = 10 ** (ripple / 10) - 1
    k = math.tan(math.pi * cutoff)
    f = np.linspace(0.0001, 0.4999, 301) * 1000
    t = np.tan(np.pi * f / 1000)
    expected = 1 / (1 + eps2 * _cheb_t(order, k / t if high else t / k) ** 2)
    got = np.abs(sos_response(sos, f, 1000.0)) ** 2
    assert np.allclose(got, expected, rtol=1e-9, atol=1e-11)
    edge = abs(sos_response(sos, [cutoff * 1000], 1000.0)[0]) ** 2
    assert edge == pytest.approx(1 / (1 + eps2), rel=1e-9)
    end = abs(sos_response(sos, [500.0 if high else 0.0], 1000.0)[0])
    assert end == pytest.approx(1.0 if order % 2 else 10 ** (-ripple / 20), rel=1e-12)


@pytest.mark.parametrize("design", [chebyshev1_lowpass, chebyshev1_highpass])
@pytest.mark.parametrize(
    "args",
    [
        (0, 1.0, 1.0, 8.0),
        (2, 0.0, 1.0, 8.0),
        (2, -1.0, 1.0, 8.0),
        (2, math.nan, 1.0, 8.0),
        (2, math.inf, 1.0, 8.0),
        (2, 200.5, 1.0, 8.0),
        (2, 4000.0, 1.0, 8.0),
        (2, True, 1.0, 8.0),
        (2, 1.0, 0.0, 8.0),
        (2, 1.0, 4.0, 8.0),
        (2, 1.0, 1.0, 0.0),
        (2.0, 1.0, 1.0, 8.0),
    ],
)
def test_chebyshev1_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize("high", [False, True])
@pytest.mark.parametrize("order", [1, 2, 3, 6, 9])
@pytest.mark.parametrize(
    ("atten", "cutoff"), [(20.0, 0.01), (40.0, 0.2), (60.0, 0.49), (100.0, 0.25)]
)
def test_chebyshev2_magnitude_has_the_closed_form(
    high: bool, order: int, atten: float, cutoff: float
) -> None:
    design = chebyshev2_highpass if high else chebyshev2_lowpass
    sos = design(order, atten, cutoff * 1000, 1000.0)
    assert sos.shape == ((order + 1) // 2, 6)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    eps2 = 1 / (10 ** (atten / 10) - 1)
    k = math.tan(math.pi * cutoff)
    f = np.linspace(0.0001, 0.4999, 301) * 1000
    t = np.tan(np.pi * f / 1000)
    x = eps2 * _cheb_t(order, t / k if high else k / t) ** 2
    got = np.abs(sos_response(sos, f, 1000.0)) ** 2
    assert np.allclose(got, x / (1 + x), rtol=1e-9, atol=1e-11)
    stop = got[f > cutoff * 1000] if not high else got[f < cutoff * 1000]
    assert np.all(stop <= 10 ** (-atten / 10) * (1 + 1e-9) + 1e-15)
    edge = abs(sos_response(sos, [cutoff * 1000], 1000.0)[0]) ** 2
    assert edge == pytest.approx(10 ** (-atten / 10), rel=1e-9)
    end = abs(sos_response(sos, [500.0 if high else 0.0], 1000.0)[0])
    assert end == pytest.approx(1.0, rel=1e-12)


def test_chebyshev2_order_1_has_its_zero_at_the_far_end() -> None:
    assert abs(sos_response(chebyshev2_lowpass(1, 30.0, 100.0, 1000.0), [500.0], 1000.0)[0]) < 1e-15
    assert abs(sos_response(chebyshev2_highpass(1, 30.0, 100.0, 1000.0), [0.0], 1000.0)[0]) < 1e-15


def test_attenuation_and_ripple_may_be_200_db() -> None:
    assert chebyshev2_lowpass(4, 200.0, 100.0, 1000.0).shape == (2, 6)
    assert chebyshev1_highpass(4, 200.0, 100.0, 1000.0).shape == (2, 6)


@pytest.mark.parametrize("design", [chebyshev2_lowpass, chebyshev2_highpass])
@pytest.mark.parametrize(
    "args",
    [
        (0, 40.0, 1.0, 8.0),
        (2, 0.0, 1.0, 8.0),
        (2, -1.0, 1.0, 8.0),
        (2, math.nan, 1.0, 8.0),
        (2, math.inf, 1.0, 8.0),
        (2, 200.5, 1.0, 8.0),
        (2, 4000.0, 1.0, 8.0),
        (2, True, 1.0, 8.0),
        (2, 40.0, 0.0, 8.0),
        (2, 40.0, 4.0, 8.0),
        (2, 40.0, 1.0, 0.0),
        (2.0, 40.0, 1.0, 8.0),
    ],
)
def test_chebyshev2_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize(
    "make",
    [
        lambda: butterworth_lowpass(4, 1e-9, 1.0),
        lambda: butterworth_highpass(4, 0.499999999, 1.0),
        lambda: chebyshev1_lowpass(4, 1.0, 1e-9, 1.0),
        lambda: chebyshev2_lowpass(4, 40.0, 1e-9, 1.0),
        lambda: chebyshev2_highpass(4, 40.0, 0.499999999, 1.0),
        lambda: butterworth_lowpass(1001, 0.1, 1.0),
    ],
)
def test_designs_that_round_onto_the_unit_circle_are_rejected(make: Any) -> None:
    with pytest.raises(ValueError):
        make()


def test_designs_near_the_limit_are_still_stable() -> None:
    for sos in (butterworth_lowpass(4, 1e-6, 1.0), chebyshev2_lowpass(4, 40.0, 1e-6, 1.0)):
        assert abs(sos_response(sos, [0.0], 1.0)[0]) == pytest.approx(1.0, rel=1e-9)


def test_tiny_db_values_keep_their_digits() -> None:
    ripple = 1e-9
    sos = chebyshev1_lowpass(3, ripple, 100.0, 1000.0)
    edge = abs(sos_response(sos, [100.0], 1000.0)[0]) ** 2
    assert 1 - edge == pytest.approx(math.expm1(ripple * math.log(10) / 10), rel=1e-5)
    sos2 = chebyshev2_lowpass(3, 1e-9, 100.0, 1000.0)
    assert all(abs(r[5]) < 1 and abs(r[4]) < 1 + r[5] for r in sos2)


@pytest.mark.parametrize("bad", [[True], [0.25 + 1j], ["x"]])
def test_sos_response_rejects_non_real_frequencies(bad: list[Any]) -> None:
    with pytest.raises(ValueError):
        sos_response([[1, 0, 0, 1, -0.5, 0]], bad, 1.0)


_BAND_CHEBYSHEVS = {
    (1, False): chebyshev1_bandpass,
    (1, True): chebyshev1_bandstop,
    (2, False): chebyshev2_bandpass,
    (2, True): chebyshev2_bandstop,
}


@pytest.mark.parametrize("kind", [1, 2])
@pytest.mark.parametrize("stop", [False, True])
@pytest.mark.parametrize("order", [1, 2, 3, 6])
@pytest.mark.parametrize(
    ("band", "db"),
    [((0.001, 0.002), 0.5), ((0.1, 0.11), 3.0), ((0.05, 0.45), 40.0), ((0.3, 0.45), 80.0)],
)
def test_chebyshev_band_magnitude_has_the_closed_form(
    kind: int, stop: bool, order: int, band: tuple[float, float], db: float
) -> None:
    sos = _BAND_CHEBYSHEVS[kind, stop](order, db, band[0] * 1000, band[1] * 1000, 1000.0)
    assert sos.shape == (order, 6)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    lo, hi = math.tan(math.pi * band[0]), math.tan(math.pi * band[1])
    w2, bw = lo * hi, hi - lo
    ratio = 10 ** (db / 10) - 1
    f = np.linspace(-0.4999, 0.4999, 301) * 1000
    t = np.abs(np.tan(np.pi * f / 1000))
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        x = bw * t / (w2 - t * t) if stop else (t * t - w2) / (bw * t)
        if kind == 1:
            expected = 1 / (1 + ratio * _cheb_t(order, x) ** 2)
        else:
            y = _cheb_t(order, 1 / x) ** 2 / ratio
            expected = 1 / (1 + 1 / y)
    got = np.abs(sos_response(sos, f, 1000.0)) ** 2
    assert np.allclose(got, expected, rtol=1e-8, atol=1e-10)
    edges = np.abs(sos_response(sos, [band[0] * 1000, band[1] * 1000], 1000.0)) ** 2
    assert edges == pytest.approx([1 / (1 + ratio)] * 2, rel=1e-8)


def test_chebyshev_band_reference_gains() -> None:
    center = (
        1000 / math.pi * math.atan(math.sqrt(math.tan(math.pi * 0.1) * math.tan(math.pi * 0.2)))
    )
    for order, want in [(3, 1.0), (4, 10 ** (-1 / 20))]:  # even type I: the ripple's low point
        bp = chebyshev1_bandpass(order, 1.0, 100.0, 200.0, 1000.0)
        bs = chebyshev1_bandstop(order, 1.0, 100.0, 200.0, 1000.0)
        assert abs(sos_response(bp, [center], 1000.0)[0]) == pytest.approx(want, rel=1e-9)
        assert np.abs(sos_response(bs, [0.0, 500.0], 1000.0)) == pytest.approx([want] * 2, rel=1e-9)
    bp2 = chebyshev2_bandpass(4, 40.0, 100.0, 200.0, 1000.0)
    bs2 = chebyshev2_bandstop(4, 40.0, 100.0, 200.0, 1000.0)
    assert abs(sos_response(bp2, [center], 1000.0)[0]) == pytest.approx(1.0, rel=1e-9)
    assert np.abs(sos_response(bs2, [0.0, 500.0], 1000.0)) == pytest.approx([1.0, 1.0], rel=1e-9)


@pytest.mark.parametrize("design", list(_BAND_CHEBYSHEVS.values()))
@pytest.mark.parametrize(
    "args",
    [
        (0, 1.0, 0.1, 0.2, 1.0),
        (1001, 1.0, 0.1, 0.2, 1.0),
        (2, 0.0, 0.1, 0.2, 1.0),
        (2, 250.0, 0.1, 0.2, 1.0),
        (2, math.nan, 0.1, 0.2, 1.0),
        (2, 1.0, 0.2, 0.1, 1.0),
        (2, 1.0, 0.1, 0.5, 1.0),
        (2, 1.0, 0.0, 0.2, 1.0),
        (2, 1.0, 0.1, 0.2, 0.0),
        (4, 1.0, 1e-9, 2e-9, 1.0),
    ],
)
def test_chebyshev_band_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize("high", [False, True])
@pytest.mark.parametrize(
    ("order", "ripple", "atten", "cutoff"),
    [(1, 1.0, 40.0, 0.1), (2, 0.5, 20.0, 0.2), (3, 0.1, 60.0, 0.05), (5, 1.0, 80.0, 0.3),
     (6, 3.0, 30.0, 0.25), (9, 0.01, 120.0, 0.1), (12, 0.5, 100.0, 0.4)],
)  # fmt: skip
def test_elliptic_is_equiripple_in_both_bands(
    high: bool, order: int, ripple: float, atten: float, cutoff: float
) -> None:
    sos = (elliptic_highpass if high else elliptic_lowpass)(order, ripple, atten, cutoff, 1.0)
    assert sos.shape == ((order + 1) // 2, 6)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    pass_lo, stop_hi = 10 ** (-ripple / 10), 10 ** (-atten / 10)
    f = np.linspace(0.0, 0.5, 200001)
    h2 = np.abs(sos_response(sos, f, 1.0)) ** 2
    passband = f >= cutoff if high else f <= cutoff
    assert np.all(h2[passband] <= 1 + 1e-12) and np.all(h2[passband] >= pass_lo * (1 - 1e-12))
    assert h2[passband].max() == pytest.approx(1.0, abs=1e-6)
    edge = np.abs(sos_response(sos, [cutoff], 1.0)[0]) ** 2
    assert edge == pytest.approx(pass_lo, rel=1e-10)
    # Stop band: from the first frequency (moving away from the pass band) at the stop level on.
    order_f = np.argsort(-f) if high else np.argsort(f)
    below = np.flatnonzero(h2[order_f] <= stop_hi * (1 + 1e-9))
    stop = order_f[below[0] :]
    assert np.all(h2[stop] <= stop_hi * (1 + 1e-6))
    if order > 1:
        assert h2[stop].max() == pytest.approx(stop_hi, rel=1e-3)
    ref = np.abs(sos_response(sos, [0.5 if high else 0.0], 1.0)[0])
    assert ref == pytest.approx(1.0 if order % 2 else 10 ** (-ripple / 20), rel=1e-12)


def test_elliptic_order_1_is_chebyshev1() -> None:
    np.testing.assert_allclose(
        elliptic_lowpass(1, 1.0, 40.0, 100.0, 1000.0),
        chebyshev1_lowpass(1, 1.0, 100.0, 1000.0),
        rtol=1e-13,
        atol=1e-15,
    )


@pytest.mark.parametrize("design", [elliptic_lowpass, elliptic_highpass])
@pytest.mark.parametrize(
    "args",
    [
        (0, 1.0, 40.0, 0.1, 1.0),
        (1001, 1.0, 40.0, 0.1, 1.0),
        (4, 0.0, 40.0, 0.1, 1.0),
        (4, 40.0, 40.0, 0.1, 1.0),
        (4, 50.0, 40.0, 0.1, 1.0),
        (4, 1.0, 250.0, 0.1, 1.0),
        (4, math.nan, 40.0, 0.1, 1.0),
        (4, 1.0, math.inf, 0.1, 1.0),
        (4, 1.0, 40.0, 0.5, 1.0),
        (4, 1.0, 40.0, 0.0, 1.0),
        (1000, 1.0, 2.0, 0.1, 1.0),
    ],
)
def test_elliptic_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize("stop", [False, True])
@pytest.mark.parametrize(
    ("order", "ripple", "atten", "band"),
    [(1, 1.0, 40.0, (0.1, 0.2)), (2, 0.5, 30.0, (0.001, 0.002)), (3, 0.1, 60.0, (0.1, 0.11)),
     (4, 1.0, 80.0, (0.05, 0.45)), (7, 0.2, 100.0, (0.3, 0.45))],
)  # fmt: skip
def test_elliptic_band_is_the_lowpass_through_the_band_map(
    stop: bool, order: int, ripple: float, atten: float, band: tuple[float, float]
) -> None:
    design = elliptic_bandstop if stop else elliptic_bandpass
    sos = design(order, ripple, atten, band[0] * 1000, band[1] * 1000, 1000.0)
    assert sos.shape == (order, 6)
    for row in sos:
        assert np.all(np.abs(np.roots(row[3:])) < 1)
    lo, hi = math.tan(math.pi * band[0]), math.tan(math.pi * band[1])
    w2, bw = lo * hi, hi - lo
    f = np.linspace(0.0005, 0.4995, 999)
    t = np.tan(np.pi * f)
    x = np.abs(bw * t / (w2 - t * t) if stop else (t * t - w2) / (bw * t))
    lowpass = elliptic_lowpass(order, ripple, atten, 0.25, 1.0)  # prewarped edge 1
    want = np.abs(sos_response(lowpass, np.arctan(x) / np.pi, 1.0)) ** 2
    got = np.abs(sos_response(sos, f * 1000, 1000.0)) ** 2
    assert np.allclose(got, want, rtol=1e-8, atol=1e-12)
    edges = np.abs(sos_response(sos, [band[0] * 1000, band[1] * 1000], 1000.0)) ** 2
    assert edges == pytest.approx([10 ** (-ripple / 10)] * 2, rel=1e-8)


def test_elliptic_band_reference_gains() -> None:
    center = (
        1000 / math.pi * math.atan(math.sqrt(math.tan(math.pi * 0.1) * math.tan(math.pi * 0.2)))
    )
    for order, want in [(3, 1.0), (4, 10 ** (-1 / 20))]:  # even: the ripple's low point
        bp = elliptic_bandpass(order, 1.0, 50.0, 100.0, 200.0, 1000.0)
        bs = elliptic_bandstop(order, 1.0, 50.0, 100.0, 200.0, 1000.0)
        assert abs(sos_response(bp, [center], 1000.0)[0]) == pytest.approx(want, rel=1e-9)
        assert np.abs(sos_response(bs, [0.0, 500.0], 1000.0)) == pytest.approx([want] * 2, rel=1e-9)
        # The band-stop's center is the prototype's infinity: a zero (odd) or the stop level.
        null = abs(sos_response(bs, [center], 1000.0)[0])
        assert null == pytest.approx(0.0 if order % 2 else 10 ** (-50 / 20), abs=1e-12)


@pytest.mark.parametrize("design", [elliptic_bandpass, elliptic_bandstop])
@pytest.mark.parametrize(
    "args",
    [
        (0, 1.0, 40.0, 0.1, 0.2, 1.0),
        (1001, 1.0, 40.0, 0.1, 0.2, 1.0),
        (2, 0.0, 40.0, 0.1, 0.2, 1.0),
        (2, 40.0, 40.0, 0.1, 0.2, 1.0),
        (2, 1.0, 250.0, 0.1, 0.2, 1.0),
        (2, math.nan, 40.0, 0.1, 0.2, 1.0),
        (2, 1.0, 40.0, 0.2, 0.1, 1.0),
        (2, 1.0, 40.0, 0.1, 0.5, 1.0),
        (2, 1.0, 40.0, 0.0, 0.2, 1.0),
        (2, 1.0, 40.0, 0.1, 0.2, 0.0),
        (4, 1.0, 40.0, 1e-9, 2e-9, 1.0),
        (1000, 1.0, 2.0, 0.1, 0.2, 1.0),
    ],
)
def test_elliptic_band_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


@pytest.mark.parametrize("high", [False, True])
@pytest.mark.parametrize("order", range(1, 11))
def test_bessel_is_3db_at_the_cutoff_and_monotonic(high: bool, order: int) -> None:
    design = bessel_highpass if high else bessel_lowpass
    sos = design(order, 0.15, 1.0)
    assert np.abs(sos_response(sos, [0.15], 1.0)[0]) ** 2 == pytest.approx(0.5, abs=1e-12)
    assert np.abs(sos_response(sos, [0.5 if high else 0.0], 1.0)[0]) == pytest.approx(1, abs=1e-13)
    h = np.abs(sos_response(sos, np.linspace(0.0, 0.5, 501), 1.0))
    assert np.all(np.diff(h) > 0) if high else np.all(np.diff(h) < 0)


@pytest.mark.parametrize("stop", [False, True])
@pytest.mark.parametrize("order", range(1, 11))
def test_bessel_band_is_the_low_pass_at_the_transformed_frequency(stop: bool, order: int) -> None:
    # A low-pass at fs/4 has K = 1, so its gain at fs/pi atan(|x|) is the prototype's at |x|.
    fs, low, high = 1.0, 0.12, 0.3
    sos = (bessel_bandstop if stop else bessel_bandpass)(order, low, high, fs)
    lp = bessel_lowpass(order, fs / 4, fs)
    lo, hi = math.tan(math.pi * low), math.tan(math.pi * high)
    f = np.linspace(0.005, 0.495, 199)
    t = np.tan(np.pi * f)
    x = (
        np.abs(hi - lo) * t / np.abs(lo * hi - t * t)
        if stop
        else np.abs(t * t - lo * hi) / ((hi - lo) * t)
    )
    want = np.abs(sos_response(lp, np.arctan(x) / np.pi, fs))
    np.testing.assert_allclose(np.abs(sos_response(sos, f, fs)), want, rtol=1e-9, atol=1e-12)
    edges = np.abs(sos_response(sos, [low, high], fs)) ** 2
    np.testing.assert_allclose(edges, 0.5, atol=1e-12)
    assert len(sos) == order


def test_bessel_band_order_1_is_butterworth() -> None:
    for design, other in (
        (bessel_bandpass, butterworth_bandpass),
        (bessel_bandstop, butterworth_bandstop),
    ):
        np.testing.assert_allclose(
            design(1, 100.0, 300.0, 1000.0), other(1, 100.0, 300.0, 1000.0), rtol=1e-15, atol=1e-16
        )


@pytest.mark.parametrize("design", [bessel_bandpass, bessel_bandstop])
@pytest.mark.parametrize(
    "args", [(0, 0.1, 0.2, 1.0), (11, 0.1, 0.2, 1.0), (3, 0.2, 0.1, 1.0), (3, 0.1, 0.5, 1.0)]
)
def test_bessel_band_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)


def test_bessel_order_1_is_butterworth() -> None:
    for design, other in (
        (bessel_lowpass, butterworth_lowpass),
        (bessel_highpass, butterworth_highpass),
    ):
        np.testing.assert_allclose(design(1, 100.0, 1000.0), other(1, 100.0, 1000.0), rtol=1e-15)


def _group_delay(sos: NDArray[np.float64], f: NDArray[np.float64]) -> NDArray[np.float64]:
    df = 1e-6
    hi, lo = sos_response(sos, f + df, 1.0), sos_response(sos, f - df, 1.0)
    return np.asarray(-np.angle(hi / lo) / (2 * np.pi * 2 * df), dtype=np.float64)


def test_bessel_delay_is_flat_where_butterworths_is_not() -> None:
    # At a cutoff well below fs/2 the bilinear transform keeps the analog delay's shape: the
    # Bessel delay is flat over half the pass band, the Butterworth's is not.
    f = np.linspace(0.0005, 0.01, 40)
    for order in (4, 6, 10):
        gd = _group_delay(bessel_lowpass(order, 0.02, 1.0), f)
        assert np.ptp(gd) / gd.mean() < 0.005
        gb = _group_delay(butterworth_lowpass(order, 0.02, 1.0), f)
        assert np.ptp(gb) / gb.mean() > 0.05


def test_bessel_order_2_delay_at_dc() -> None:
    # theta_2(w0 s) has delay w0 a_1/a_0 = w0 at DC; the bilinear map adds a factor 1/(2K).
    k = math.tan(math.pi * 0.02)
    w0 = math.sqrt(3 * (math.sqrt(5) - 1) / 2)
    gd = _group_delay(bessel_lowpass(2, 0.02, 1.0), np.array([1e-5]))
    assert gd[0] == pytest.approx(w0 / (2 * k), rel=1e-6)


@pytest.mark.parametrize("design", [bessel_lowpass, bessel_highpass])
@pytest.mark.parametrize(
    "args",
    [(0, 0.1, 1.0), (11, 0.1, 1.0), (-1, 0.1, 1.0), (4, 0.5, 1.0), (4, 0.0, 1.0),
     (4, math.nan, 1.0), (4, 0.1, math.inf), (4, 0.1, 0.0)],
)  # fmt: skip
def test_bessel_rejects_bad_arguments(design: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        design(*args)
