"""The end-to-end QPSK link and its JSON report."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from signalforge import QpskLinkConfig, qpsk_link

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
