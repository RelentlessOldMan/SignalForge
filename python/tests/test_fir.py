"""FIR design and the streaming FIR filter (conventions: FIR filters)."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import (
    FirFilter,
    convolve,
    fir_bandpass,
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
