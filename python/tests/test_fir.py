"""FIR design and the streaming FIR filter (conventions: FIR filters)."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import (
    FirFilter,
    convolve,
    fir_bandpass,
    fir_equiripple,
    fir_highpass,
    fir_lowpass,
    fir_response,
    kaiser_parameters,
)


def test_kaiser_design_meets_its_spec() -> None:
    # 60 dB, 50 Hz transition centered on 200 Hz at fs = 1000: the passband to 175 Hz stays within
    # the ripple and the stopband from 225 Hz stays below -60 dB (3 dB margin for the formula).
    n, beta = kaiser_parameters(60, 50, 1000)
    h = fir_lowpass(n, 200, 1000, window="kaiser", beta=beta)
    delta = 10 ** (-57 / 20)
    passband = np.abs(fir_response(h, np.linspace(0, 175, 200), 1000))
    stopband = np.abs(fir_response(h, np.linspace(225, 500, 300), 1000))
    assert np.max(np.abs(passband - 1)) < delta
    assert np.max(stopband) < delta


@pytest.mark.parametrize(
    "taps",
    [
        fir_lowpass(31, 100, 1000),
        fir_highpass(31, 100, 1000, window="hann"),
        fir_bandpass(30, 100, 200, 1000, window="blackman"),
    ],
)
def test_designs_are_symmetric(taps: NDArray[np.float64]) -> None:
    np.testing.assert_allclose(taps, taps[::-1], rtol=0, atol=1e-15)


def test_reference_gains_are_one() -> None:
    assert abs(fir_response(fir_lowpass(25, 80, 1000), [0], 1000)[0] - 1) < 1e-14
    assert abs(abs(fir_response(fir_highpass(25, 80, 1000), [500], 1000)[0]) - 1) < 1e-14
    assert abs(abs(fir_response(fir_bandpass(25, 80, 300, 1000), [190], 1000)[0]) - 1) < 1e-14


def test_numpy_scalars_are_accepted_and_bools_rejected() -> None:
    h = fir_lowpass(np.int64(11), np.float64(100), np.float64(1000))  # type: ignore[arg-type]
    np.testing.assert_array_equal(h, fir_lowpass(11, 100.0, 1000.0))
    with pytest.raises(ValueError):
        fir_lowpass(11, True, 1000)
    with pytest.raises(ValueError):
        fir_lowpass(11.0, 100, 1000)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        kaiser_parameters(float("nan"), 10, 100)
    with pytest.raises(ValueError):
        kaiser_parameters(60, 1e-300, 100)


@pytest.mark.parametrize("complex_input", [False, True])
def test_any_split_matches_convolution(complex_input: bool) -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(500)
    if complex_input:
        x = x + 1j * rng.standard_normal(500)
    h = fir_lowpass(17, 120, 1000)
    want = convolve(x, h)[: x.size]
    for _ in range(5):
        cuts = np.sort(rng.integers(0, x.size + 1, size=12))
        f = FirFilter(h)
        y = np.concatenate([f.process(p) for p in np.split(x, cuts)])
        assert y.dtype == (np.complex128 if complex_input else np.float64)
        np.testing.assert_allclose(y, want, rtol=0, atol=1e-13)


def test_reset_and_kind() -> None:
    f = FirFilter([1.0, 1.0])
    assert f.process([]).size == 0
    np.testing.assert_array_equal(f.process([1.0, 2.0]), [1.0, 3.0])
    with pytest.raises(ValueError, match="real"):
        f.process([1j])
    assert f.process(np.zeros(0, dtype=complex)).size == 0  # empty chunks never raise
    f.reset()
    np.testing.assert_array_equal(f.process([1j]), [1j])  # no memory of the real samples


def test_taps_are_copied() -> None:
    taps = np.array([1.0, 2.0])
    f = FirFilter(taps)
    taps[0] = 9
    f.taps[1] = 9
    np.testing.assert_array_equal(f.taps, [1.0, 2.0])


@pytest.mark.parametrize("taps", [[], [[1.0]], [1j], [np.inf]])
def test_bad_taps(taps: object) -> None:
    with pytest.raises(ValueError):
        FirFilter(taps)  # type: ignore[arg-type]


def test_two_dimensional_chunk_raises() -> None:
    with pytest.raises(ValueError):
        FirFilter([1.0]).process([[1.0]])


def _worst(taps: NDArray[np.float64], lo: float, hi: float, want: float) -> float:
    """Largest ``|A(f) - want|`` on a dense grid over ``[lo, hi]`` (normalized frequency)."""
    t = np.arange(taps.size) - (taps.size - 1) / 2
    f = np.linspace(lo, hi, 4001)
    return float(np.max(np.abs(np.cos(2 * np.pi * np.outer(f, t)) @ taps - want)))


@pytest.mark.parametrize("n", [40, 41])
def test_equiripple_errors_are_level_across_bands(n: int) -> None:
    h = fir_equiripple(n, [0, 0.1, 0.15, 0.5], [1, 0], 1)
    np.testing.assert_allclose(h, h[::-1], rtol=0, atol=1e-15)
    passband, stopband = _worst(h, 0, 0.1, 1), _worst(h, 0.15, 0.5, 0)
    assert passband == pytest.approx(stopband, rel=0.02)
    w = fir_equiripple(n, [0, 0.1, 0.15, 0.5], [1, 0], 1, weights=[1, 10])
    assert _worst(w, 0, 0.1, 1) == pytest.approx(10 * _worst(w, 0.15, 0.5, 0), rel=0.02)
    assert _worst(w, 0.15, 0.5, 0) < stopband < _worst(w, 0, 0.1, 1)
    if n % 2 == 0:
        assert abs(float(np.sum(h * (-1.0) ** np.arange(n)))) < 1e-15  # type II: H(fs/2) = 0


def test_equiripple_beats_a_windowed_design_and_improves_with_length() -> None:
    bands = [0, 0.1, 0.15, 0.5]
    h = fir_equiripple(41, bands, [1, 0], 1)
    windowed = fir_lowpass(41, 0.125, 1)
    worst = max(_worst(h, 0, 0.1, 1), _worst(h, 0.15, 0.5, 0))
    assert worst < max(_worst(windowed, 0, 0.1, 1), _worst(windowed, 0.15, 0.5, 0))
    longer = fir_equiripple(61, bands, [1, 0], 1)
    assert max(_worst(longer, 0, 0.1, 1), _worst(longer, 0.15, 0.5, 0)) < worst / 2


def test_equiripple_accepts_arrays_and_scales_with_sample_rate() -> None:
    bands = [0, 0.1, 0.15, 0.5]
    h = fir_equiripple(31, bands, [1, 0], 1)
    np.testing.assert_array_equal(h, fir_equiripple(31, np.array(bands), np.array([1, 0]), 1))
    np.testing.assert_array_equal(h, fir_equiripple(31, bands, [1, 0], 1, weights=[1, 1]))
    hz = fir_equiripple(31, [b * 48000 for b in bands], [1, 0], 48000)
    np.testing.assert_allclose(hz, h, rtol=0, atol=1e-15)


@pytest.mark.parametrize("n", [45, 51, 61, 101, 301])
def test_equiripple_near_the_precision_limit_raises_or_meets_its_bound(n: int) -> None:
    try:
        h = fir_equiripple(n, [0, 0.1, 0.4, 0.5], [1, 0], 1)
    except ValueError as e:
        assert "beyond double precision" in str(e)
    else:
        assert max(_worst(h, 0, 0.1, 1), _worst(h, 0.4, 0.5, 0)) < 1e-9


def test_equiripple_bad_arguments() -> None:
    with pytest.raises(ValueError):
        fir_equiripple(21, [0, 0.1, np.nan, 0.5], [1, 0], 1)
    with pytest.raises(ValueError):
        fir_equiripple(21, [[0, 0.1], [0.2, 0.5]], [1, 0], 1)
    with pytest.raises(ValueError):
        fir_equiripple(21, [0, 0.1, 0.2, 0.5], [1, np.inf], 1)
    with pytest.raises(ValueError):
        fir_equiripple(21, [0, 0.1, 0.2, 0.5], [1, 0], 1, weights=[1, np.nan])
    with pytest.raises(ValueError):
        fir_equiripple(21, [0, 0.1, 0.2, 0.5], [1, 0], 1, grid_density=2.5)  # type: ignore[arg-type]
