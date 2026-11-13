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


@pytest.mark.parametrize(("up", "down"), [(3, 2), (2, 3), (1, 4), (5, 1), (4, 6)])
def test_resampler_is_resample_with_delayed_taps(up: int, down: int) -> None:
    rng = np.random.default_rng(7)
    x = rng.standard_normal(301)
    r = sf.Resampler(up, down)
    cuts = np.sort(rng.integers(0, x.size, 9))
    y = np.concatenate([r.process(c) for c in np.split(x, cuts)])
    h = np.concatenate((np.zeros(r.taps.size - 1), r.taps))
    assert y.size == -(-x.size * (up // np.gcd(up, down)) // (down // np.gcd(up, down)))
    assert np.allclose(y, sf.resample(x, up, down, h), rtol=0, atol=1e-12)


def test_resampler_complex_even_taps_and_reset() -> None:
    x = np.exp(1j * 0.3 * np.arange(50))
    taps = [0.2, 0.5, 0.3, -0.1]
    r = sf.Resampler(7, 3, taps)
    first = np.concatenate([r.process(x[:13]), r.process(x[13:13]), r.process(x[13:])])
    assert np.iscomplexobj(first)
    r.reset()
    assert np.array_equal(r.process(x), first)
    assert np.allclose(first, sf.resample(x, 7, 3, [0, 0, 0, *taps]), rtol=0, atol=1e-12)


def test_resampler_one_one_copies_and_empty_chunk() -> None:
    r = sf.Resampler(2, 2)
    assert np.array_equal(r.taps, [1.0])
    assert r.process([]).size == 0
    assert np.array_equal(r.process([1.0, 2.0]), [1.0, 2.0])


def test_resampler_kind_is_fixed_until_reset() -> None:
    r = sf.Resampler(3, 2)
    r.process([1.0])
    with pytest.raises(ValueError):
        r.process([1j])
    r.reset()
    assert np.iscomplexobj(r.process([1j]))


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.Resampler(0, 1),
        lambda: sf.Resampler(1, 0),
        lambda: sf.Resampler(2, 1, []),
        lambda: sf.Resampler(2, 1, [1.0, np.nan]),
        lambda: sf.Resampler(2, 1).process([[1.0]]),
    ],
)
def test_resampler_bad_arguments(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        call()
