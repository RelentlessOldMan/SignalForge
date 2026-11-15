"""Least-squares FIR design: optimality, against equiripple, type II, errors (conventions: FIR
filters, Least-squares design)."""

import numpy as np
import pytest

import signalforge as sf

BANDS = [0.0, 0.1, 0.15, 0.5]
DESIRED = [1.0, 1.0, 0.0, 0.0]


def _energy(h: np.ndarray, bands: list[float], desired: list[float], weights: list[float]) -> float:
    """The weighted integral squared error by the trapezoid rule on 20001 points per band."""
    c = (h.size - 1) / 2
    total = 0.0
    for j in range(len(weights)):
        nu = np.linspace(bands[2 * j], bands[2 * j + 1], 20001)
        a = np.real(sf.fir_response(h, nu, 1) * np.exp(2j * np.pi * nu * c))
        d = np.interp(nu, bands[2 * j : 2 * j + 2], desired[2 * j : 2 * j + 2])
        e = (a - d) ** 2
        total += weights[j] * float(np.sum((e[1:] + e[:-1]) / 2) * (nu[1] - nu[0]))
    return total


@pytest.mark.parametrize("n", [31, 30])
def test_symmetric_perturbations_only_raise_the_error(n: int) -> None:
    h = sf.fir_least_squares(n, BANDS, DESIRED, 1, [1, 4])
    assert np.allclose(h, h[::-1], rtol=0, atol=1e-15)
    best = _energy(h, BANDS, DESIRED, [1, 4])
    rng = np.random.default_rng(5)
    for _ in range(5):
        d = rng.standard_normal(n)
        d = 1e-3 * (d + d[::-1])
        assert _energy(h + d, BANDS, DESIRED, [1, 4]) > best


def test_lower_error_energy_than_equiripple() -> None:
    ls = sf.fir_least_squares(41, BANDS, DESIRED, 1)
    eq = sf.fir_equiripple(41, BANDS, [1, 0], 1)
    assert _energy(ls, BANDS, DESIRED, [1, 1]) < _energy(eq, BANDS, DESIRED, [1, 1])


def test_even_taps_have_a_zero_at_nyquist() -> None:
    h = sf.fir_least_squares(16, [0, 0.2, 0.3, 0.5], [0, 0, 1, 1], 1)
    assert abs(sf.fir_response(h, [0.5], 1)[0]) < 1e-12


def test_sloped_band_is_followed() -> None:
    h = sf.fir_least_squares(61, [0, 0.4], [0, 0.8], 1)
    nu = np.linspace(0.05, 0.35, 7)
    a = np.real(sf.fir_response(h, nu, 1) * np.exp(2j * np.pi * nu * 30))
    assert np.allclose(a, 2 * nu, rtol=0, atol=1e-3)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.fir_least_squares(0, BANDS, DESIRED, 1),
        lambda: sf.fir_least_squares(1002, BANDS, DESIRED, 1),
        lambda: sf.fir_least_squares(2.5, BANDS, DESIRED, 1),  # type: ignore[arg-type]
        lambda: sf.fir_least_squares(11, BANDS, [1, 0], 1),
        lambda: sf.fir_least_squares(11, [0, 0.2, 0.3], DESIRED, 1),
        lambda: sf.fir_least_squares(11, [0, 0.2, 0.2, 0.5], DESIRED, 1),
        lambda: sf.fir_least_squares(11, [0, 0.2, 0.3, 0.6], DESIRED, 1),
        lambda: sf.fir_least_squares(11, BANDS, DESIRED, 1, [1, 0]),
        lambda: sf.fir_least_squares(11, BANDS, DESIRED, 1, [1]),
        lambda: sf.fir_least_squares(11, BANDS, [1, np.nan, 0, 0], 1),
        lambda: sf.fir_least_squares(11, BANDS, DESIRED, 0),
    ],
)
def test_bad_arguments(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        call()


def _anti_energy(h: np.ndarray, bands: list[float], target: list[float], diff: bool) -> float:
    """The integral squared error of antisymmetric taps, A = sum h[n] sin(2 pi nu (n - c))."""
    t = np.arange(h.size) - (h.size - 1) / 2
    total = 0.0
    for j in range(len(bands) // 2):
        nu = np.linspace(bands[2 * j], bands[2 * j + 1], 20001)
        a = np.sin(2 * np.pi * np.outer(nu, t)) @ h
        d = np.interp(nu, bands[2 * j : 2 * j + 2], target[2 * j : 2 * j + 2])
        if diff:
            d = -2 * np.pi * nu * d
        total += float(np.trapezoid((a - d) ** 2, nu))
    return total


@pytest.mark.parametrize("n", [9, 10])
@pytest.mark.parametrize("kind", ["hilbert", "differentiator"])
def test_antisymmetric_perturbations_only_raise_the_error(n: int, kind: str) -> None:
    bands, target = [0.0, 0.3, 0.35, 0.5], [1.0, 1.0, 0.0, 0.0]
    if kind == "hilbert":
        bands, target = [0.04, 0.46], [1.0, 1.0]
    h = sf.fir_least_squares(n, bands, target, 1.0, kind=kind)
    np.testing.assert_array_equal(h, -h[::-1])
    best = _anti_energy(h, bands, target, kind == "differentiator")
    rng = np.random.default_rng(5)
    for _ in range(10):
        dh = rng.standard_normal(n) * 1e-3
        dh = (dh - dh[::-1]) / 2
        for s in (1, -1):
            assert _anti_energy(h + s * dh, bands, target, kind == "differentiator") > best


def test_differentiator_follows_the_slope() -> None:
    h = sf.fir_least_squares(41, [0, 0.3, 0.4, 0.5], [1, 1, 0, 0], 1.0, [1, 1], "differentiator")
    nu = np.linspace(0.01, 0.28, 40)
    t = np.arange(41) - 20
    a = np.sin(2 * np.pi * np.outer(nu, t)) @ h
    np.testing.assert_allclose(a, -2 * np.pi * nu, atol=1e-3)
    assert h[20] == 0


def test_antisymmetric_bad_arguments() -> None:
    with pytest.raises(ValueError):
        sf.fir_least_squares(11, BANDS, DESIRED, 1.0, kind="bandstop")
    with pytest.raises(ValueError):
        sf.fir_least_squares(1, BANDS, DESIRED, 1.0, kind="hilbert")
