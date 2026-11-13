"""Resampling: analytic tones, DC level, gcd reduction, errors (conventions: Resampling)."""

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(("up", "down"), [(3, 2), (2, 3), (4, 1), (1, 4), (5, 3)])
def test_tone_matches_analytic_tone_in_interior(up: int, down: int) -> None:
    n = np.arange(4000)
    f = 0.02
    y = sf.resample(np.cos(2 * np.pi * f * n + 0.4), up, down)
    t = np.arange(y.size) * down / up
    assert y.size == -(-n.size * up // down)
    assert np.max(np.abs(y - np.cos(2 * np.pi * f * t + 0.4))[300:-300]) < 5e-3


def test_complex_tone_keeps_phase() -> None:
    n = np.arange(2000)
    y = sf.resample(np.exp(1j * 0.1 * n), 2, 1)
    t = np.arange(y.size) / 2
    assert np.iscomplexobj(y)
    assert np.max(np.abs(y - np.exp(1j * 0.1 * t))[200:-200]) < 5e-3


def test_dc_level_is_kept() -> None:
    y = sf.interpolate(np.full(300, 2.0), 3)
    assert np.allclose(y[100:-100], 2.0, atol=1e-2)


def test_gcd_reduction() -> None:
    x = np.sin(np.arange(50) * 0.3)
    assert np.array_equal(sf.resample(x, 6, 4), sf.resample(x, 3, 2))
    assert np.array_equal(sf.resample_taps(6, 4), sf.resample_taps(3, 2))


def test_default_taps_are_the_documented_lowpass() -> None:
    assert np.array_equal(sf.resample_taps(3, 2), sf.fir_lowpass(61, 1 / 6, 1))


def test_identity_returns_copy() -> None:
    x = np.array([1.0, 2.0])
    y = sf.resample(x, 2, 2)
    assert np.array_equal(y, x) and y is not x


def test_wrappers() -> None:
    x = np.arange(20.0)
    assert np.array_equal(sf.interpolate(x, 3), sf.resample(x, 3, 1))
    assert np.array_equal(sf.decimate(x, 3), sf.resample(x, 1, 3))


def test_numpy_integer_factors() -> None:
    x = np.arange(10.0)
    assert np.array_equal(sf.resample(x, np.int64(2), np.int32(1)), sf.resample(x, 2, 1))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.resample([1.0], 0, 1),
        lambda: sf.resample([1.0], 1, -1),
        lambda: sf.resample([1.0], 2.0, 1),  # type: ignore[arg-type]
        lambda: sf.resample([1.0], True, 1),
        lambda: sf.resample([1.0], 2, np.True_),  # type: ignore[arg-type]
        lambda: sf.resample([], 2, 1),
        lambda: sf.resample([[1.0]], 2, 1),
        lambda: sf.resample([1.0], 2, 1, [0.5, 0.5]),
        lambda: sf.resample([1.0], 2, 1, []),
        lambda: sf.resample([1.0], 2, 1, [1.0, np.inf, 1.0]),
        lambda: sf.resample([1.0], 2, 1, [1j, 1, 1j]),
        lambda: sf.resample_taps(3, 3),
        lambda: sf.decimate([1.0], 0),
        lambda: sf.interpolate([1.0], 0),
    ],
)
def test_bad_arguments(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        call()
