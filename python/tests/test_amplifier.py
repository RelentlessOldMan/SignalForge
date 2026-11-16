"""Saleh and Rapp amplifier models (conventions: Channel, Amplifier models; ADR 0114)."""

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import am_am_pm, gain_compression, rapp_amplifier, saleh_amplifier

TWT = (2.1587, 1.1517, 4.0033, 9.1040)


def _sweep(
    lo_db: float, hi_db: float, step: float
) -> tuple[NDArray[np.float64], NDArray[np.complex128]]:
    edges = np.arange(lo_db, hi_db + step / 2, step)
    rad = 10 ** ((edges[:-1] + edges[1:]) / 2 / 20)
    th = np.array([0.2, 1.9, -2.4])
    x = (rad[:, None] * np.exp(1j * th)[None, :]).ravel()
    return np.asarray(edges, dtype=np.float64), np.asarray(x, dtype=np.complex128)


def test_am_am_pm_reads_the_saleh_curves_back() -> None:
    aa, ba, ap, bp = TWT
    edges, x = _sweep(-30.0, 10.0, 0.5)
    r = am_am_pm(x, saleh_amplifier(x, *TWT), edges)
    rad = 10 ** (r.levels_db / 20)
    np.testing.assert_allclose(r.gain_db, 20 * np.log10(aa / (1 + ba * rad**2)), atol=1e-10)
    phi = ap * rad**2 / (1 + bp * rad**2)
    np.testing.assert_allclose(r.phase_deg, np.degrees(phi), atol=1e-10)


def test_saleh_output_peaks_at_one_over_root_beta() -> None:
    aa, ba = TWT[0], TWT[1]
    r = np.linspace(0.01, 3, 30001)
    out = np.abs(saleh_amplifier(r, *TWT))
    k = int(np.argmax(out))
    assert r[k] == pytest.approx(1 / math.sqrt(ba), abs=1e-4)
    assert out[k] == pytest.approx(aa / (2 * math.sqrt(ba)), rel=1e-9)


@pytest.mark.parametrize("p", [0.5, 1.0, 2.0, 5.0])
def test_gain_compression_finds_rapps_one_db_point(p: float) -> None:
    g, a_sat = 3.0, 0.5
    edges, x = _sweep(-160.0, 20.0, 0.02)
    r = am_am_pm(x, rapp_amplifier(x, g, a_sat, p), edges)
    np.testing.assert_allclose(r.phase_deg, 0.0, atol=1e-12)
    c = gain_compression(r.levels_db, r.levels_db + r.gain_db)
    expected = 20 * math.log10(a_sat / g * (10 ** (p / 10) - 1) ** (1 / (2 * p)))
    assert c.input_point_db == pytest.approx(expected, abs=1e-3)
    assert c.small_signal_gain_db == pytest.approx(20 * math.log10(g), abs=1e-5)


def test_rapp_is_continuous_at_the_knee_and_saturates() -> None:
    g, a_sat, p = 2.0, 1.0, 1.5
    knee = a_sat / g
    y = rapp_amplifier([knee * (1 - 1e-12), knee, knee * (1 + 1e-12)], g, a_sat, p)
    np.testing.assert_allclose(np.abs(y), a_sat / 2 ** (1 / (2 * p)), rtol=1e-11)
    big = rapp_amplifier([1e200j, -1e300 + 0j], g, a_sat, p)
    np.testing.assert_allclose(big, [1j * a_sat, -a_sat], rtol=1e-15)


def test_real_input_and_zero() -> None:
    y = saleh_amplifier(np.array([0.0, -0.5]), *TWT)
    assert y.dtype == np.complex128
    assert y[0] == 0
    assert math.degrees(np.angle(y[1])) == pytest.approx(
        -180 + math.degrees(TWT[2] * 0.25 / (1 + TWT[3] * 0.25))
    )
    assert rapp_amplifier([], 1.0, 1.0, 1.0).size == 0


@pytest.mark.parametrize(
    "params",
    [
        (0.0, 1.0, 1.0, 1.0),
        (1.0, -1.0, 1.0, 1.0),
        (1.0, 1.0, 1.0, -1.0),
        (1.0, 1.0, math.inf, 1.0),
        (True, 1.0, 1.0, 1.0),
    ],
)
def test_saleh_bad_arguments(params: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValueError):
        saleh_amplifier([1.0], *params)


@pytest.mark.parametrize(
    "params", [(0.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 0.0), (1.0, 1.0, math.nan)]
)
def test_rapp_bad_arguments(params: tuple[float, float, float]) -> None:
    with pytest.raises(ValueError):
        rapp_amplifier([1.0], *params)


def test_two_dimensional_samples_are_rejected() -> None:
    with pytest.raises(ValueError):
        rapp_amplifier([[1.0]], 1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        saleh_amplifier([[1.0]], *TWT)
