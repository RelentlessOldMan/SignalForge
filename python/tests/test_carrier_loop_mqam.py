"""8-PSK and 16-QAM carrier loops: closed forms and tracking (conventions: Synchronization,
Tracking loops)."""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf

Mapper = Callable[[NDArray[np.uint8]], NDArray[np.complex128]]
Loop = Callable[..., sf.CarrierRecovery]
CASES: list[tuple[Mapper, Loop, Callable[..., NDArray[np.uint8]], int]] = [
    (sf.psk8_map, sf.psk8_carrier_tracking, sf.psk8_demap_hard, 3),
    (sf.qam16_map, sf.qam16_carrier_tracking, sf.qam16_demap_hard, 4),
]


def _rotated(
    mapper: Mapper, k: int, nsym: int, theta0: float, omega: float
) -> tuple[NDArray[np.uint8], NDArray[np.complex128], NDArray[np.float64]]:
    bits = sf.prbs(15, k * nsym)
    theta = np.asarray(theta0 + omega * np.arange(nsym), dtype=np.float64)
    return bits, np.asarray(mapper(bits) * np.exp(1j * theta), dtype=np.complex128), theta


def test_psk8_proportional_lag_is_exact() -> None:
    omega, kp = 0.01, 0.1
    _, z, theta = _rotated(sf.psk8_map, 3, 1000, 0.1, omega)
    r = sf.psk8_carrier_tracking(z, kp, 0.0)
    # e = sin(theta - phi) for unit symbols, so the step kp*e = omega at the lag
    np.testing.assert_allclose((theta - r.phases)[500:], math.asin(omega / kp), rtol=0, atol=1e-9)


@pytest.mark.parametrize(("mapper", "loop", "demap", "k"), CASES)
def test_integrator_removes_the_lag(mapper: Mapper, loop: Loop, demap: object, k: int) -> None:
    omega = 0.004
    kp, ki = sf.pi_loop_gains(0.02, 1 / math.sqrt(2), 1.0)
    _, z, theta = _rotated(mapper, k, 4000, 0.1, omega)
    r = loop(z, kp, ki)
    np.testing.assert_allclose((theta - r.phases)[3000:], 0, rtol=0, atol=1e-8)
    np.testing.assert_allclose(np.diff(r.phases)[3000:], omega, rtol=1e-6)


@pytest.mark.parametrize(("mapper", "loop", "demap", "k"), CASES)
def test_tracks_through_noise_without_errors(
    mapper: Mapper, loop: Loop, demap: Callable[..., NDArray[np.uint8]], k: int
) -> None:
    # at Es/N0 22 dB both have a symbol error rate below 1e-7 with perfect phase
    nsym = 3000
    bits, z, _ = _rotated(mapper, k, nsym, 0.15, 0.003)
    y = sf.awgn(z, 22.0, seed=7)
    kp, ki = sf.pi_loop_gains(0.02, 1 / math.sqrt(2), 1.0)
    r = loop(y, kp, ki)
    got = demap(r.symbols[300:])
    assert sf.bit_errors(bits[k * 300 :], got).errors == 0


def test_psk8_locks_to_a_multiple_of_pi_over_4() -> None:
    _, z, _ = _rotated(sf.psk8_map, 3, 400, math.pi / 4 + 0.05, 0.0)
    r = sf.psk8_carrier_tracking(z, 0.1, 0.0)
    np.testing.assert_allclose(r.phases[-1], 0.05, atol=1e-9)


@pytest.mark.parametrize("loop", [sf.psk8_carrier_tracking, sf.qam16_carrier_tracking])
@pytest.mark.parametrize(
    "bad",
    [
        {"kp": -0.1},
        {"ki": math.nan},
        {"phase": math.inf},
        {"symbols": [1, complex(math.nan, 0)]},
        {"symbols": [[1, 1]]},
    ],
)
def test_bad_arguments_raise(loop: Loop, bad: dict[str, object]) -> None:
    args: dict[str, object] = {"symbols": [1, 1j], "kp": 0.1, "ki": 0.01} | bad
    with pytest.raises(ValueError):
        loop(args.pop("symbols"), args.pop("kp"), args.pop("ki"), **args)
