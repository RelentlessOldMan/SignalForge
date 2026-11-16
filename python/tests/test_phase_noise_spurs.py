"""Phase noise with spurs removed (conventions: Phase noise with spurs removed; ADR 0115)."""

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import integrated_phase_noise, phase_noise, phase_noise_ssb

FS = 1.0e6
N = 1 << 16


def _carrier_with_noise(linewidth: float, seed: int) -> NDArray[np.complex128]:
    t = np.arange(N)
    x = np.exp(2j * np.pi * 125_000.0 * t / FS)
    return phase_noise(x, linewidth, FS, seed=seed)


def _spur(offset: float, dbc: float) -> NDArray[np.complex128]:
    t = np.arange(N)
    return np.asarray(10 ** (dbc / 20) * np.exp(2j * np.pi * (125_000.0 + offset) * t / FS))


@pytest.mark.parametrize("seed", [1, 2])
def test_removal_recovers_the_integral_without_the_spur(seed: int) -> None:
    clean = _carrier_with_noise(20.0, seed)
    spur_at = 1600 * FS / N  # coherent: 100 bins of a 4096 segment from the carrier
    dirty = clean + _spur(spur_at, -20.0)
    base = integrated_phase_noise(clean, FS, 1_000.0, 50_000.0, nperseg=4096)
    kept = integrated_phase_noise(dirty, FS, 1_000.0, 50_000.0, nperseg=4096)
    gone = integrated_phase_noise(
        dirty, FS, 1_000.0, 50_000.0, nperseg=4096, spur_offsets=[spur_at]
    )
    # the spur adds its own power (-20 dBc) on top of the noise
    added = 10 ** (kept.integrated_dbc / 10) - 10 ** (base.integrated_dbc / 10)
    assert added == pytest.approx(1e-2, rel=0.05)
    assert gone.integrated_dbc == pytest.approx(base.integrated_dbc, abs=0.05)


def test_l_at_the_spur_reads_the_noise_around_it() -> None:
    clean = _carrier_with_noise(20.0, 3)
    spur_at = 1600 * FS / N
    dirty = clean + _spur(spur_at, -20.0)
    offsets = [spur_at]
    base = phase_noise_ssb(clean, FS, offsets, nperseg=4096).l_dbc_hz[0]
    kept = phase_noise_ssb(dirty, FS, offsets, nperseg=4096).l_dbc_hz[0]
    gone = phase_noise_ssb(dirty, FS, offsets, nperseg=4096, spur_offsets=offsets).l_dbc_hz[0]
    assert kept > base + 15
    assert gone == pytest.approx(base, abs=1.5)


def test_no_spurs_changes_nothing() -> None:
    x = _carrier_with_noise(50.0, 4)
    a = integrated_phase_noise(x, FS, 3_000.0, 20_000.0, nperseg=2048)
    b = integrated_phase_noise(x, FS, 3_000.0, 20_000.0, nperseg=2048, spur_offsets=[])
    assert (a.integrated_dbc, a.phase_rms) == (b.integrated_dbc, b.phase_rms)
    c = phase_noise_ssb(x, FS, [5_000.0], nperseg=2048, spur_offsets=None)
    d = phase_noise_ssb(x, FS, [5_000.0], nperseg=2048, spur_offsets=[])
    np.testing.assert_array_equal(c.l_dbc_hz, d.l_dbc_hz)


def test_a_spur_outside_the_band_does_not_change_the_integral() -> None:
    x = _carrier_with_noise(50.0, 5)
    a = integrated_phase_noise(x, FS, 3_000.0, 20_000.0, nperseg=2048)
    b = integrated_phase_noise(x, FS, 3_000.0, 20_000.0, nperseg=2048, spur_offsets=[100_000.0])
    assert a.integrated_dbc == b.integrated_dbc


@pytest.mark.parametrize("spurs", [[[1_000.0]], [0.0], [-5.0], [math.nan], [math.inf]])
def test_bad_spur_offsets(spurs: object) -> None:
    x = _carrier_with_noise(50.0, 6)
    with pytest.raises(ValueError):
        integrated_phase_noise(x, FS, 3_000.0, 20_000.0, spur_offsets=spurs)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        phase_noise_ssb(x, FS, [5_000.0], spur_offsets=spurs)  # type: ignore[arg-type]
