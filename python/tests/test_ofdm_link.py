"""OFDM in the link (conventions: QPSK link, OFDM; ADR 0063)."""

from __future__ import annotations

import json
import math
from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

FS = 4000.0  # default symbol_rate times samples_per_symbol
U = 63  # default subcarriers: all 64 but DC


def _ofdm(**kw: Any) -> QpskLinkConfig:
    return QpskLinkConfig(modulation="ofdm", **{"num_symbols": U * 20, "preamble_symbols": U, **kw})


@pytest.mark.parametrize(
    ("delay", "f", "phase"), [(0, 0.0, 0.0), (37, 7.3, 1.1), (5, -30.0, -2.5), (130, 29.0, 3.0)]
)
def test_noiseless_recovers_everything(delay: int, f: float, phase: float) -> None:
    r = qpsk_link(_ofdm(delay_samples=delay, frequency_offset_hz=f, phase=phase))
    assert (r.frame_start, r.timing_offset) == (delay // 4, float(delay % 4))
    assert r.frequency_offset_hz == pytest.approx(f, abs=1e-9)
    want = math.remainder(phase + 2 * math.pi * f * delay / FS, 2 * math.pi)
    assert r.phase_offset is not None
    assert abs(math.remainder(r.phase_offset - want, 2 * math.pi)) < 1e-9
    assert r.evm is not None and r.evm.rms < 1e-12
    assert r.bit_errors.errors == 0 and r.bit_errors.compared == 2 * U * 20
    assert r.ber_theory is None


def test_one_block_and_a_short_prefix() -> None:
    sc = (-3, -1, 2, 3)
    r = qpsk_link(
        _ofdm(
            num_symbols=4,
            preamble_symbols=4,
            ofdm_nfft=8,
            ofdm_cp_len=1,
            ofdm_subcarriers=sc,
            delay_samples=3,
        )
    )
    assert (r.frame_start, r.timing_offset, r.bit_errors.errors) == (0, 3.0, 0)
    assert r.config.ofdm_subcarriers == sc


def test_ber_between_known_channel_and_estimate_loss() -> None:
    p, eb, errors, compared = 8, 6.0, 0, 0
    for seed in range(4):
        r = qpsk_link(
            _ofdm(
                num_symbols=U * 200,
                preamble_symbols=U * p,
                eb_n0_db=eb,
                seed=seed,
                frequency_offset_hz=-20.0,
                phase=0.3,
                delay_samples=11,
            )
        )
        assert r.frame_start == 2
        errors += r.bit_errors.errors
        compared += r.bit_errors.compared
    low = sf.qpsk_ber_theory(eb)
    high = sf.qpsk_ber_theory(eb - 10 * math.log10(1 + 1 / p))
    assert r.ber_theory == low
    ber, sd = errors / compared, math.sqrt(high / compared)
    assert low - 4 * sd < ber < high + 4 * sd


def test_noise_is_per_data_subcarrier() -> None:
    # Known channel (no offsets), many preamble blocks: EVM^2 is the per-subcarrier N0/Es.
    eb = 10.0
    r = qpsk_link(_ofdm(num_symbols=U * 200, preamble_symbols=U * 200, eb_n0_db=eb))
    assert r.evm is not None
    n0 = 1 / (2 * 10 ** (eb / 10))
    assert r.evm.rms**2 == pytest.approx(n0, rel=0.05)


@pytest.mark.parametrize(
    "kw",
    [
        {"num_symbols": U * 20 + 1},
        {"preamble_symbols": U + 1},
        {"ofdm_nfft": 1},
        {"ofdm_cp_len": 0},
        {"ofdm_cp_len": 65},
        {"ofdm_subcarriers": ()},
        {"ofdm_subcarriers": (1, 1), "num_symbols": 2, "preamble_symbols": 2},
        {"ofdm_subcarriers": (32,)},
        {"ofdm_subcarriers": (True,)},
        {"ofdm_subcarriers": "12"},
        {"frequency_offset_hz": 31.25},
        {"phase_noise_linewidth_hz": 1.0},
        {"clock_offset_ppm": 10.0},
        {"timing_loop_gains": (0.01, 0.0)},
        {"carrier_loop_gains": (0.01, 0.0)},
        {"rolloff": 2.0},
    ],
)
def test_rejects(kw: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        qpsk_link(_ofdm(**kw))


def test_ofdm_fields_are_checked_for_other_modulations() -> None:
    with pytest.raises(ValueError):
        qpsk_link(QpskLinkConfig(num_symbols=64, ofdm_cp_len=0))
    r = qpsk_link(QpskLinkConfig(num_symbols=64, ofdm_subcarriers=[3, -2]))  # type: ignore[arg-type]
    assert r.config.ofdm_subcarriers == (3, -2)
    assert json.loads(r.to_json())["config"]["ofdm_subcarriers"] == [3, -2]
