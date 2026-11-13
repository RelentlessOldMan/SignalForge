"""Group delay: against a numerical phase derivative, cascades, flat Bessel delay, errors
(conventions: FIR filters and IIR filters, Group delay)."""

import numpy as np
import pytest

import signalforge as sf


def _phase_slope(response, f: np.ndarray, fs: float) -> np.ndarray:  # type: ignore[no-untyped-def]
    """-dphi/dw by a central difference of the phase, step 1e-6 of fs (independent check)."""
    d = 1e-6 * fs
    ratio = response(f + d) / response(f - d)
    return np.asarray(-np.angle(ratio) / (2 * np.pi * 2 * d / fs))


def test_fir_matches_the_phase_derivative() -> None:
    h = np.random.default_rng(3).standard_normal(17)
    f = np.linspace(10.0, 3990.0, 37)
    tau = sf.fir_group_delay(h, f, 8000)
    num = _phase_slope(lambda g: sf.fir_response(h, g, 8000), f, 8000.0)
    assert np.allclose(tau, num, rtol=0, atol=1e-5 * (1 + np.abs(num)))


def test_sos_matches_the_phase_derivative_and_cascades_add() -> None:
    s = sf.chebyshev1_lowpass(6, 1.0, 0.2, 1.0)
    f = np.linspace(0.001, 0.499, 41)
    tau = sf.sos_group_delay(s, f, 1)
    num = _phase_slope(lambda g: sf.sos_response(s, g, 1), f, 1.0)
    assert np.allclose(tau, num, rtol=0, atol=1e-5 * (1 + np.abs(num)))
    parts = sum(sf.sos_group_delay(s[i : i + 1], f, 1) for i in range(len(s)))
    assert np.allclose(tau, parts, rtol=1e-12, atol=1e-12)


def test_linear_phase_taps_delay_half_their_length() -> None:
    h = sf.fir_lowpass(41, 0.1, 1)
    tau = sf.fir_group_delay(h, np.linspace(0, 0.09, 10), 1)
    assert np.allclose(tau, 20, rtol=0, atol=1e-9)


def test_bessel_delay_is_flat_where_butterworth_is_not() -> None:
    f = np.linspace(0, 0.05, 11)
    bessel = sf.sos_group_delay(sf.bessel_lowpass(5, 0.05, 1), f, 1)
    butter = sf.sos_group_delay(sf.butterworth_lowpass(5, 0.05, 1), f, 1)
    assert np.max(np.abs(bessel[:6] / bessel[0] - 1)) < 0.01
    assert np.max(bessel) / np.min(bessel) < 1.03
    assert np.max(butter) / np.min(butter) > 1.3


def test_nan_only_at_the_zero() -> None:
    tau = sf.sos_group_delay([[1, 1, 0, 1, 0, 0]], [0.49, 0.5], 1)
    assert tau[0] == pytest.approx(0.5) and np.isnan(tau[1])


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.fir_group_delay([], [0.0], 1),
        lambda: sf.fir_group_delay([1.0], [np.nan], 1),
        lambda: sf.fir_group_delay([1.0], [[0.0]], 1),
        lambda: sf.fir_group_delay([1.0], [0.0], 0),
        lambda: sf.sos_group_delay([[1, 0, 0, 0, 0, 0]], [0.0], 1),
        lambda: sf.sos_group_delay([[1, 0, 0, 1, 0]], [0.0], 1),
        lambda: sf.sos_group_delay([[1, 0, 0, 1, 0, 0]], [1j], 1),
        lambda: sf.sos_group_delay([[1, 0, 0, 1, 0, 0]], [np.inf], 1),
    ],
)
def test_bad_arguments(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        call()
