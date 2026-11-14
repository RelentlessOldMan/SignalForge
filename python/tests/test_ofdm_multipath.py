"""Multipath in the OFDM link (conventions: QPSK link, OFDM; ADR 0064)."""

from __future__ import annotations

import cmath
import json
import math
from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

FS = 4000.0  # default symbol_rate times samples_per_symbol
U = 63  # default subcarriers: all 64 but DC
DELAYS = (0, 2, 5, 8)
GAINS = ((1.0, 0.0), (0.5, -0.3), (-0.2, 0.4), (0.1, 0.1))


def _ofdm(**kw: Any) -> QpskLinkConfig:
    base = {"num_symbols": U * 20, "preamble_symbols": U, "modulation": "ofdm"}
    return QpskLinkConfig(**{**base, **kw})


def _power(k: int, n: int = 64) -> float:
    """|H_k|^2 of DELAYS/GAINS, the DFT of the impulse response written out."""
    h = sum(
        complex(*g) * cmath.exp(-2j * math.pi * k * d / n)
        for d, g in zip(DELAYS, GAINS, strict=True)
    )
    return abs(h) ** 2


def _theory(eb: float) -> float:
    ks = [k for k in range(-32, 32) if k != 0]
    return sum(sf.qpsk_ber_theory(eb + 10 * math.log10(_power(k))) for k in ks) / len(ks)


@pytest.mark.parametrize(("delay", "f", "phase"), [(0, 0.0, 0.0), (37, 7.3, 1.1), (130, -29.0, 3)])
def test_noiseless_recovers_every_bit(delay: int, f: float, phase: float) -> None:
    r = qpsk_link(
        _ofdm(
            delay_samples=delay,
            frequency_offset_hz=f,
            phase=phase,
            multipath_delays=DELAYS,
            multipath_gains=GAINS,
        )
    )
    start = 4 * r.frame_start + int(r.timing_offset)
    assert delay <= start <= delay + max(DELAYS)
    # the prefix's first samples carry the previous block's echo: f is biased a little
    assert r.frequency_offset_hz == pytest.approx(f, abs=0.05)
    assert r.evm is not None and r.evm.rms < 0.01
    assert r.bit_errors.errors == 0


@pytest.mark.parametrize(("tap", "gain"), [(0, (1.0, 0.0)), (3, (0.0, -2.0)), (8, (-0.6, 0.8))])
def test_one_path_is_a_delay_and_a_gain(tap: int, gain: tuple[float, float]) -> None:
    delay, f, phase = 21, 13.0, -0.4
    r = qpsk_link(
        _ofdm(
            delay_samples=delay,
            frequency_offset_hz=f,
            phase=phase,
            multipath_delays=(tap,),
            multipath_gains=(gain,),
        )
    )
    total = delay + tap
    assert (r.frame_start, r.timing_offset) == (total // 4, float(total % 4))
    assert r.frequency_offset_hz == pytest.approx(f, abs=1e-9)
    # the path comes before the carrier offset, which is phase 0 at sample 0
    want = phase + 2 * math.pi * f * total / FS + math.atan2(gain[1], gain[0])
    assert r.phase_offset is not None
    assert abs(math.remainder(r.phase_offset - want, 2 * math.pi)) < 1e-9
    assert r.evm is not None and r.evm.rms < 1e-12
    assert r.bit_errors.errors == 0


def test_ber_theory_is_the_mean_over_subcarriers() -> None:
    r = qpsk_link(_ofdm(eb_n0_db=7.0, multipath_delays=DELAYS, multipath_gains=GAINS))
    assert r.ber_theory == pytest.approx(_theory(7.0), rel=1e-12)
    flat = qpsk_link(_ofdm(eb_n0_db=7.0, multipath_delays=(4,), multipath_gains=((0.0, 1.0),)))
    assert flat.ber_theory == pytest.approx(sf.qpsk_ber_theory(7.0), rel=1e-12)


@pytest.mark.parametrize("eb", [4.0, 10.0])
def test_ber_between_known_channel_and_estimate_loss(eb: float) -> None:
    # each run's channel estimate is shared by all its blocks, so its error does not average out
    # over the blocks: enough preamble blocks keep that spread well inside the bracket
    p, errors, compared = 64, 0, 0
    for seed in range(3):
        r = qpsk_link(
            _ofdm(
                num_symbols=U * 400,
                preamble_symbols=U * p,
                eb_n0_db=eb,
                seed=seed,
                frequency_offset_hz=-20.0,
                delay_samples=11,
                multipath_delays=DELAYS,
                multipath_gains=GAINS,
            )
        )
        errors += r.bit_errors.errors
        compared += r.bit_errors.compared
    low, high = _theory(eb), _theory(eb - 10 * math.log10(1 + 1 / p))
    ber, sd = errors / compared, math.sqrt(high / compared)
    assert low - 4 * sd < ber < high + 4 * sd


@pytest.mark.parametrize(
    "kw",
    [
        {"multipath_delays": (9,), "multipath_gains": ((1.0, 0.0),)},  # more than cp // 2 = 8
        {"multipath_delays": (0, 1), "multipath_gains": ((1.0, 0.0),)},
        {"multipath_delays": (), "multipath_gains": ()},
        {"multipath_delays": (0,)},
        {"multipath_gains": ((1.0, 0.0),)},
        {"multipath_delays": (True,), "multipath_gains": ((1.0, 0.0),)},
        {"multipath_delays": (-1,), "multipath_gains": ((1.0, 0.0),)},
        {"multipath_delays": (1.5,), "multipath_gains": ((1.0, 0.0),)},
        {"multipath_delays": (0,), "multipath_gains": ((1.0,),)},
        {"multipath_delays": (0,), "multipath_gains": ("10",)},
        {"multipath_delays": (0,), "multipath_gains": ((math.nan, 0.0),)},
        {"multipath_delays": "0", "multipath_gains": ((1.0, 0.0),)},
    ],
)
def test_rejects(kw: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        qpsk_link(_ofdm(**kw))


def test_other_modulations_take_no_multipath() -> None:
    with pytest.raises(ValueError):
        qpsk_link(QpskLinkConfig(num_symbols=64, multipath_delays=(0,), multipath_gains=((1, 0),)))


def test_report_config() -> None:
    r = qpsk_link(_ofdm(multipath_delays=[0, 3], multipath_gains=[[1, 0], [0, 0.5]]))
    assert r.config.multipath_delays == (0, 3)
    assert r.config.multipath_gains == ((1.0, 0.0), (0.0, 0.5))
    cfg = json.loads(r.to_json())["config"]
    assert (cfg["multipath_delays"], cfg["multipath_gains"]) == ([0, 3], [[1.0, 0.0], [0.0, 0.5]])
    assert json.loads(qpsk_link(_ofdm()).to_json())["config"]["multipath_gains"] is None
