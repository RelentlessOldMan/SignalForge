"""The end-to-end QPSK link and its JSON report."""

from __future__ import annotations

import dataclasses
import json
import math

import numpy as np
import pytest

from signalforge import QpskLinkConfig, pi_loop_gains, qpsk_link

# The JSON field names; the C# tests check the same list.
REPORT_KEYS = [
    "config",
    "timing_offset",
    "frame_start",
    "frequency_offset_hz",
    "phase_offset",
    "evm",
    "bit_errors",
    "ber_theory",
]
CONFIG_KEYS = [
    "num_symbols",
    "eb_n0_db",
    "symbol_rate",
    "samples_per_symbol",
    "rolloff",
    "span_symbols",
    "delay_samples",
    "frequency_offset_hz",
    "phase",
    "preamble_symbols",
    "phase_block_symbols",
    "prbs_order",
    "seed",
    "modulation",
    "phase_noise_linewidth_hz",
    "clock_offset_ppm",
    "timing_loop_gains",
    "carrier_loop_gains",
]


@pytest.mark.parametrize(
    ("df", "phase", "delay"), [(0.0, 1.0, 2), (20.0, -2.5, 3), (-60.0, 0.4, 0)]
)
def test_ber_matches_theory_at_6_db(df: float, phase: float, delay: int) -> None:
    cfg = QpskLinkConfig(
        num_symbols=100_000,
        eb_n0_db=6.0,
        delay_samples=delay,
        frequency_offset_hz=df,
        phase=phase,
        seed=3,
    )
    r = qpsk_link(cfg)
    assert r.ber_theory is not None
    # theory 2.39e-3 over 200k bits is about 480 errors; offsets before the matched filter add a
    # little interference, so allow 20%
    assert abs(r.bit_errors.rate / r.ber_theory - 1) < 0.2
    assert abs(r.frequency_offset_hz - df) < 0.01
    assert r.evm.num_symbols == 100_000


def test_json_report_shape() -> None:
    r = qpsk_link(QpskLinkConfig(num_symbols=64, eb_n0_db=8.0))
    d = json.loads(r.to_json())
    assert list(d) == REPORT_KEYS
    assert list(d["config"]) == CONFIG_KEYS
    assert list(d["evm"]) == ["rms", "rms_percent", "rms_db", "peak", "peak_index", "num_symbols"]
    assert list(d["bit_errors"]) == ["errors", "compared", "rate"]
    assert d["config"]["eb_n0_db"] == 8.0
    assert isinstance(d["frame_start"], int)
    assert d["bit_errors"]["compared"] == 128


def test_noiseless_report_has_null_theory() -> None:
    d = json.loads(qpsk_link(QpskLinkConfig(num_symbols=50)).to_json())
    assert d["ber_theory"] is None
    assert d["config"]["eb_n0_db"] is None


def test_non_finite_numbers_are_strings() -> None:
    from signalforge.link import _encode

    assert _encode({"a": math.inf, "b": {"c": -math.inf, "d": math.nan}, "e": 1.5}) == {
        "a": "inf",
        "b": {"c": "-inf", "d": "nan"},
        "e": 1.5,
    }


@pytest.mark.parametrize(
    "bad",
    [
        {"num_symbols": 2.0},
        {"num_symbols": 50, "seed": -1},
        {"num_symbols": 50, "phase": math.inf},
        {"num_symbols": 50, "symbol_rate": True},
        {"num_symbols": 50, "prbs_order": 8},
        {"num_symbols": 50, "rolloff": 1.5},
        {"num_symbols": 50, "clock_offset_ppm": 2e5},
        {"num_symbols": 50, "phase_noise_linewidth_hz": -1.0},
        {"num_symbols": 50, "timing_loop_gains": (0.1,)},
        {"num_symbols": 50, "timing_loop_gains": (0.1, -0.01)},
        {"num_symbols": 50, "carrier_loop_gains": (0.1, math.nan)},
        {"num_symbols": 50, "carrier_loop_gains": "ab"},
        {"num_symbols": 50, "modulation": "psk8"},
        {"num_symbols": 50, "modulation": 4},
    ],
)
def test_rejects(bad: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        qpsk_link(QpskLinkConfig(**bad))  # type: ignore[arg-type]


def test_numpy_scalars_are_accepted_and_serialize() -> None:
    cfg = QpskLinkConfig(
        num_symbols=np.int64(50),  # type: ignore[arg-type]
        eb_n0_db=np.int64(8),  # type: ignore[arg-type]
        phase=np.float32(0.5),  # type: ignore[arg-type]
        symbol_rate=2000,
    )
    r = qpsk_link(cfg)
    d = json.loads(r.to_json())
    assert d["config"]["num_symbols"] == 50
    assert d["config"]["eb_n0_db"] == 8.0
    assert type(r.config.num_symbols) is int
    assert type(r.config.symbol_rate) is float


# gains for a loop bandwidth of 0.01 per symbol: the Gardner detector's slope on this pulse is about
# 0.26 (measured open loop, test_timing_loop), the carrier detector's sqrt2 at unit amplitude
TIMING = pi_loop_gains(0.01, 1 / math.sqrt(2), 0.26)
CARRIER = pi_loop_gains(0.01, 1 / math.sqrt(2), math.sqrt(2))


def test_timing_loop_follows_a_clock_offset() -> None:
    # 400 ppm over 3000 symbols is 4.8 samples of drift, more than a symbol
    base = {
        "num_symbols": 3000,
        "eb_n0_db": 6.0,
        "clock_offset_ppm": 400.0,
        "frequency_offset_hz": 7.0,
        "phase": 0.3,
        "delay_samples": 1,
        "seed": 3,
    }
    fixed = qpsk_link(QpskLinkConfig(**base))  # type: ignore[arg-type]
    assert fixed.bit_errors.rate > 0.1
    for gains in [
        {"timing_loop_gains": TIMING},
        {"timing_loop_gains": TIMING, "carrier_loop_gains": CARRIER},
    ]:
        r = qpsk_link(QpskLinkConfig(**base, **gains))  # type: ignore[arg-type]
        assert r.ber_theory is not None
        # theory is about 14 errors in 6000 bits; 5 sd of a Poisson count is about 19
        assert r.bit_errors.errors < 14 + 19
        assert r.evm.rms < 0.4


def test_loops_off_by_default_and_without_offset_change_little() -> None:
    cfg = {"num_symbols": 2000, "eb_n0_db": 8.0, "frequency_offset_hz": -15.0, "seed": 5}
    plain = qpsk_link(QpskLinkConfig(**cfg))  # type: ignore[arg-type]
    same = qpsk_link(QpskLinkConfig(**cfg, clock_offset_ppm=0.0))  # type: ignore[arg-type]
    assert plain == same
    looped = qpsk_link(
        QpskLinkConfig(**cfg, timing_loop_gains=TIMING, carrier_loop_gains=CARRIER)  # type: ignore[arg-type]
    )
    assert abs(looped.evm.rms - plain.evm.rms) < 0.02
    assert abs(looped.bit_errors.errors - plain.bit_errors.errors) <= 10


def test_gains_serialize_as_pairs() -> None:
    r = qpsk_link(QpskLinkConfig(num_symbols=64, timing_loop_gains=[0.1, 0.001]))  # type: ignore[arg-type]
    d = json.loads(r.to_json())["config"]
    assert d["timing_loop_gains"] == [0.1, 0.001]
    assert d["carrier_loop_gains"] is None
    assert d["clock_offset_ppm"] == 0.0
    assert r.config.timing_loop_gains == (0.1, 0.001)


def test_carrier_loop_follows_phase_noise() -> None:
    # 0.15 Hz at 1000 Bd is 0.03 rad rms per symbol, wandering about 1.7 rad over 3000 symbols,
    # which one line through the block phases cannot follow; the loop at Bn 0.03 can
    gains = pi_loop_gains(0.03, 1 / math.sqrt(2), math.sqrt(2))
    block = looped = 0
    for seed in range(5):
        cfg = QpskLinkConfig(
            num_symbols=3000,
            eb_n0_db=8.0,
            phase_noise_linewidth_hz=0.15,
            frequency_offset_hz=5.0,
            seed=seed,
        )
        block += qpsk_link(cfg).bit_errors.errors
        looped += qpsk_link(dataclasses.replace(cfg, carrier_loop_gains=gains)).bit_errors.errors
    # theory 1.9e-4 is about 6 errors in 30000 bits; a cycle slip would cost hundreds
    assert block > 300
    assert looped < 40


def test_no_phase_noise_draws_nothing() -> None:
    cfg = QpskLinkConfig(num_symbols=500, eb_n0_db=5.0, seed=9)
    assert qpsk_link(cfg) == qpsk_link(dataclasses.replace(cfg, phase_noise_linewidth_hz=0.0))


@pytest.mark.parametrize(
    ("df", "phase", "delay"), [(30.0, 2.6, 1), (-90.0, -0.4, 7), (0.0, 0.0, 0)]
)
def test_qam16_noiseless_has_no_errors(df: float, phase: float, delay: int) -> None:
    r = qpsk_link(
        QpskLinkConfig(
            num_symbols=400,
            modulation="qam16",
            frequency_offset_hz=df,
            phase=phase,
            delay_samples=delay,
        )
    )
    assert r.bit_errors.compared == 1600
    assert r.bit_errors.errors == 0
    assert r.ber_theory is None


def test_qam16_ber_near_theory() -> None:
    cfg = QpskLinkConfig(
        num_symbols=20000,
        eb_n0_db=8.0,
        modulation="qam16",
        frequency_offset_hz=15.0,
        phase=-0.9,
        delay_samples=6,
        preamble_symbols=64,
        seed=21,
    )
    r = qpsk_link(cfg)
    assert r.ber_theory is not None
    expected = r.ber_theory * r.bit_errors.compared  # about 740
    assert 0.85 * expected < r.bit_errors.errors < 1.2 * expected
    assert abs(r.frequency_offset_hz - 15.0) < 0.05


def test_qam16_carrier_loop() -> None:
    gains = pi_loop_gains(0.01, 1 / math.sqrt(2), 1.0)  # 16-QAM detector slope about 1
    r = qpsk_link(
        QpskLinkConfig(
            num_symbols=2000,
            eb_n0_db=14.0,
            modulation="qam16",
            frequency_offset_hz=-12.0,
            phase=1.0,
            carrier_loop_gains=gains,
            seed=2,
        )
    )
    assert r.bit_errors.errors <= 3


def test_modulation_default_is_qpsk() -> None:
    cfg = QpskLinkConfig(num_symbols=300, eb_n0_db=6.0, frequency_offset_hz=5.0, seed=1)
    assert qpsk_link(cfg) == qpsk_link(dataclasses.replace(cfg, modulation="qpsk"))
    assert qpsk_link(cfg).bit_errors.compared == 600
