"""All-pass sections: unit magnitude, the named phases, and the total phase as the group delay's
integral (conventions: IIR filters, All-pass sections)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _phase(sos: np.ndarray, f: np.ndarray) -> np.ndarray:
    return np.unwrap(np.angle(sf.sos_response(sos, f, 1.0)))


@pytest.mark.parametrize("cutoff", [0.01, 0.1, 0.25, 0.4, 0.49])
def test_first_order_is_minus_a_quarter_turn_at_the_cutoff(cutoff: float) -> None:
    sos = sf.allpass_first_order(cutoff, 1.0)
    f = np.concatenate([np.linspace(0, cutoff, 2001), [0.5]])
    p = _phase(sos, np.sort(f))
    np.testing.assert_allclose(np.abs(sf.sos_response(sos, f, 1.0)), 1, atol=1e-13)
    assert sf.sos_response(sos, [cutoff], 1.0)[0] == pytest.approx(-1j, abs=1e-12)
    assert p[0] == 0 and np.all(np.diff(p) < 0)


@pytest.mark.parametrize(
    ("center", "bandwidth"), [(0.1, 0.05), (0.3, 0.02), (0.25, 0.2), (0.05, 0.08), (0.45, 0.4)]
)
def test_second_order_phase_points_are_a_bandwidth_apart(center: float, bandwidth: float) -> None:
    sos = sf.allpass_second_order(center, bandwidth, 1.0)
    f = np.linspace(0, 0.5, 200001)
    p = _phase(sos, f)
    assert np.all(np.diff(p) < 0) and p[-1] == pytest.approx(-2 * math.pi, abs=1e-9)
    f1, fc, f2 = (np.interp(v, -p, f) for v in (math.pi / 2, math.pi, 3 * math.pi / 2))
    assert fc == pytest.approx(center, abs=1e-6)
    assert f2 - f1 == pytest.approx(bandwidth, abs=1e-6)
    np.testing.assert_allclose(np.abs(sf.sos_response(sos, f[::1000], 1.0)), 1, atol=1e-13)


def test_group_delay_integrates_to_the_total_phase() -> None:
    f = np.linspace(0, 0.5, 100001)
    for sos, turns in (
        (sf.allpass_first_order(0.2, 1.0), 0.5),
        (sf.allpass_second_order(0.15, 0.1, 1.0), 1.0),
    ):
        tau = sf.sos_group_delay(sos, f, 1.0)
        total = np.sum((tau[1:] + tau[:-1]) / 2 * np.diff(f)) * 2 * math.pi
        assert total == pytest.approx(2 * math.pi * turns, rel=1e-8)


def test_an_allpass_keeps_a_signals_power() -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(1 << 14)
    y = sf.IirFilter(sf.allpass_second_order(0.2, 0.05, 1.0)).process(
        np.concatenate([x, np.zeros(4096)])
    )
    assert np.sum(y**2) == pytest.approx(np.sum(x**2), rel=1e-9)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.allpass_first_order(0.0, 1.0),
        lambda: sf.allpass_first_order(0.5, 1.0),
        lambda: sf.allpass_first_order(math.nan, 1.0),
        lambda: sf.allpass_second_order(0.1, 0.0, 1.0),
        lambda: sf.allpass_second_order(0.1, 0.5, 1.0),
        lambda: sf.allpass_second_order(0.5, 0.1, 1.0),
        lambda: sf.allpass_second_order(0.1, 0.1, -1.0),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
