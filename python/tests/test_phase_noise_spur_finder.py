"""The phase noise spur finder (conventions: Phase noise spur finder; ADR 0116)."""

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import integrated_phase_noise, phase_noise, phase_noise_spurs

FS = 1.0e6
N = 1 << 16
SPUR_AT = 1600 * FS / N  # coherent: 100 bins of a 4096 segment from the carrier


def _carrier_with_noise(linewidth: float, seed: int) -> NDArray[np.complex128]:
    t = np.arange(N)
    x = np.exp(2j * np.pi * 125_000.0 * t / FS)
    return phase_noise(x, linewidth, FS, seed=seed)


def _with_spur(x: NDArray[np.complex128], dbc: float) -> NDArray[np.complex128]:
    t = np.arange(N)
    return np.asarray(x + 10 ** (dbc / 20) * np.exp(2j * np.pi * (125_000.0 + SPUR_AT) * t / FS))


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_noise_alone_has_no_spurs(seed: int) -> None:
    r = phase_noise_spurs(_carrier_with_noise(20.0, seed), FS, 3_000.0, 50_000.0, nperseg=4096)
    assert r.offsets.size == 0 and r.levels_dbc.size == 0


@pytest.mark.parametrize("seed", [1, 2])
def test_a_spur_is_found_at_its_offset_and_level(seed: int) -> None:
    x = _with_spur(_carrier_with_noise(20.0, seed), -20.0)
    r = phase_noise_spurs(x, FS, 3_000.0, 50_000.0, nperseg=4096)
    assert r.offsets.size == 1
    # the right bin: the noisy carrier's centroid wanders by a few Hz
    assert r.offsets[0] == pytest.approx(SPUR_AT, abs=FS / 4096 / 2)
    assert r.levels_dbc[0] == pytest.approx(-20.0, abs=0.2)


def test_found_offsets_remove_the_spur() -> None:
    clean = _carrier_with_noise(20.0, 4)
    dirty = _with_spur(clean, -20.0)
    r = phase_noise_spurs(dirty, FS, 3_000.0, 50_000.0, nperseg=4096)
    base = integrated_phase_noise(clean, FS, 1_000.0, 50_000.0, nperseg=4096)
    gone = integrated_phase_noise(
        dirty, FS, 1_000.0, 50_000.0, nperseg=4096, spur_offsets=np.abs(r.offsets)
    )
    assert gone.integrated_dbc == pytest.approx(base.integrated_dbc, abs=0.05)


def test_a_higher_threshold_finds_fewer() -> None:
    x = _with_spur(_carrier_with_noise(20.0, 5), -20.0)
    assert phase_noise_spurs(x, FS, 3_000.0, 50_000.0, nperseg=4096).offsets.size == 1
    r = phase_noise_spurs(x, FS, 3_000.0, 50_000.0, nperseg=4096, threshold_db=60.0)
    assert r.offsets.size == 0


def test_real_input_finds_both_sides() -> None:
    n, fs = 1024, 1024.0
    t = np.arange(n)
    x = np.cos(2 * np.pi * 200 * t / n + 0.01 * np.sin(2 * np.pi * 40 * t / n))
    r = phase_noise_spurs(x, fs, 20.0, 60.0)
    np.testing.assert_allclose(r.offsets, [-40.0, 40.0], atol=1e-9)
    # J_1(0.01)^2 relative to J_0(0.01)^2, about (0.005)^2
    np.testing.assert_allclose(r.levels_dbc, 20 * math.log10(0.01 / 2), atol=1e-3)


@pytest.mark.parametrize("threshold", [0.0, -3.0, math.nan, math.inf])
def test_bad_threshold(threshold: float) -> None:
    x = _carrier_with_noise(50.0, 6)
    with pytest.raises(ValueError):
        phase_noise_spurs(x, FS, 3_000.0, 20_000.0, threshold_db=threshold)


@pytest.mark.parametrize(("lo", "hi"), [(20_000.0, 3_000.0), (0.0, 1_000.0), (3_000.0, math.inf)])
def test_bad_band(lo: float, hi: float) -> None:
    x = _carrier_with_noise(50.0, 7)
    with pytest.raises(ValueError):
        phase_noise_spurs(x, FS, lo, hi)


def test_band_too_near_the_carrier() -> None:
    x = _carrier_with_noise(50.0, 8)
    with pytest.raises(ValueError):
        phase_noise_spurs(x, FS, 100.0, 20_000.0, nperseg=4096)
