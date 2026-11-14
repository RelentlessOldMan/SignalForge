"""Phase noise and clock offset in the OFDM link (conventions: QPSK link, OFDM; ADR 0065)."""

from __future__ import annotations

import math
from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

U = 52
GUARDED = tuple(k for k in range(-26, 27) if k != 0)  # resampling cannot keep the band edge
LOOP = (0.3, 0.02)
ALLOWANCE_DB = 0.5  # leakage between subcarriers and loop jitter: a test allowance, not derived


def _ofdm(**kw: Any) -> QpskLinkConfig:
    base = {
        "modulation": "ofdm",
        "num_symbols": U * 400,
        "preamble_symbols": U * 16,
        "ofdm_subcarriers": GUARDED,
        "delay_samples": 11,
        "frequency_offset_hz": -20.0,
    }
    return QpskLinkConfig(**{**base, **kw})


@pytest.mark.parametrize("ppm", [200.0, -200.0])
def test_noiseless_clock_offset_needs_the_loop(ppm: float) -> None:
    r = qpsk_link(_ofdm(clock_offset_ppm=ppm, timing_loop_gains=LOOP))
    assert r.bit_errors.errors == 0
    assert r.evm is not None and r.evm.rms < 0.05
    off = qpsk_link(_ofdm(clock_offset_ppm=ppm))
    assert off.bit_errors.rate > 0.1


@pytest.mark.parametrize(
    "kw",
    [
        {"clock_offset_ppm": -150.0, "timing_loop_gains": LOOP},
        {"phase_noise_linewidth_hz": 0.1},
        {"timing_loop_gains": LOOP},  # the loop on a clean clock
    ],
)
def test_ber_within_the_allowance(kw: dict[str, Any]) -> None:
    eb, p, errors, compared = 6.0, 16, 0, 0
    for seed in range(3):
        r = qpsk_link(_ofdm(eb_n0_db=eb, seed=seed, **kw))
        assert r.ber_theory == sf.qpsk_ber_theory(eb)
        errors += r.bit_errors.errors
        compared += r.bit_errors.compared
    low = sf.qpsk_ber_theory(eb)
    high = sf.qpsk_ber_theory(eb - 10 * math.log10(1 + 1 / p) - ALLOWANCE_DB)
    ber, sd = errors / compared, math.sqrt(high / compared)
    assert low - 4 * sd < ber < high + 4 * sd


def test_phase_noise_noiseless() -> None:
    r = qpsk_link(_ofdm(phase_noise_linewidth_hz=0.1, seed=4))
    assert r.bit_errors.errors == 0


def test_a_long_preamble_keeps_its_phase() -> None:
    # 200 preamble blocks with the prefix's frequency error: each block is turned to block 0's
    # phase before the average, so the estimate does not smear (ADR 0065)
    r = qpsk_link(
        QpskLinkConfig(
            modulation="ofdm",
            num_symbols=63 * 200,
            preamble_symbols=63 * 200,
            eb_n0_db=10.0,
            seed=2,
        )
    )
    assert r.evm is not None
    assert r.evm.rms**2 == pytest.approx(1 / (2 * 10), rel=0.05)


@pytest.mark.parametrize(
    "kw",
    [
        {"clock_offset_ppm": 300.0},  # 300e-6 * (11 + 400 * 80) > 8
        {"clock_offset_ppm": 1.0, "multipath_delays": (8,), "multipath_gains": ((1.0, 0.0),)},
        {"carrier_loop_gains": (0.01, 0.0)},
    ],
)
def test_rejects(kw: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        qpsk_link(_ofdm(**kw))


def test_drift_at_the_margin_is_accepted() -> None:
    # 250e-6 * (11 + 400 * 80) = 8.00275 > 8 is rejected; 249 ppm is 7.97 and runs
    with pytest.raises(ValueError):
        qpsk_link(_ofdm(clock_offset_ppm=250.0))
    assert qpsk_link(_ofdm(clock_offset_ppm=-249.0, timing_loop_gains=LOOP)).bit_errors.errors == 0
