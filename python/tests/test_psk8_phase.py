"""psk8_phase_offset and psk8_block_phases (conventions: Synchronization; ADR 0051)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from signalforge import psk8_block_phases, psk8_map, psk8_phase_offset


def _symbols(n: int, seed: int = 3) -> np.typing.NDArray[np.complex128]:
    return psk8_map(np.random.default_rng(seed).integers(0, 2, 3 * n))


@pytest.mark.parametrize("phi", [-0.39, -0.1, 0.0, 0.2, 0.39])
def test_phase_inside_range_is_exact(phi: float) -> None:
    assert psk8_phase_offset(_symbols(50) * np.exp(1j * phi)) == pytest.approx(phi, abs=1e-12)


def test_phase_is_modulo_pi_over_4() -> None:
    z = _symbols(50)
    for m in range(-4, 5):
        got = psk8_phase_offset(z * np.exp(1j * (0.1 + m * math.pi / 4)))
        assert got == pytest.approx(0.1, abs=1e-12)


def test_scale_does_not_matter() -> None:
    z = _symbols(20) * np.exp(0.25j)
    for s in (1e-200, 1e-3, 1e150):
        assert psk8_phase_offset(z * s) == pytest.approx(0.25, abs=1e-12)


def test_block_phases_follow_a_ramp_past_pi_over_8() -> None:
    n, b, w = 400, 20, 0.004  # 0.08 rad per block, under pi/8
    z = _symbols(n) * np.exp(1j * (0.3 + w * np.arange(n)))
    ph = psk8_block_phases(z, b)
    mid = (np.arange(ph.size) * b + np.minimum(np.arange(ph.size) * b + b, n) - 1) / 2
    assert np.allclose(ph, 0.3 + w * mid, atol=1e-9)
    assert ph[-1] > 1.5  # unwrapped well past the first range, (-pi/8, pi/8]


def test_short_last_block() -> None:
    assert psk8_block_phases(_symbols(45), 20).size == 3


@pytest.mark.parametrize("bad", [0, -1, 2.0, True])
def test_bad_block_size(bad: object) -> None:
    with pytest.raises(ValueError):
        psk8_block_phases(_symbols(10), bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [[], [1, math.nan], [[1, 1j]]])
def test_bad_symbols(bad: object) -> None:
    with pytest.raises(ValueError):
        psk8_phase_offset(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        psk8_block_phases(bad, 2)  # type: ignore[arg-type]
