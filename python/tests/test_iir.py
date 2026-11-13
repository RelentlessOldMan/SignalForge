"""Butterworth design, section responses and the streaming IIR filter (conventions: IIR filters)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import (
    IirFilter,
    butterworth_bandpass,
    butterworth_bandstop,
    butterworth_highpass,
    butterworth_lowpass,
    chebyshev1_highpass,
    chebyshev1_lowpass,
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
