"""Pilots that correct the equalizer phase loop's cycle slips (conventions: Synchronization,
Decision-feedback equalizer; ADR 0075)."""

from __future__ import annotations

import cmath
import dataclasses
import math
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link


def _psk8(seed: int, n: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return sf.psk8_map(rng.integers(0, 2, 3 * n).astype(np.uint8))


def _jump(a: np.ndarray, at: int) -> np.ndarray:
    # an exact pi/4 turn from symbol `at` on: 8-PSK decides it as other points with no error
    return a * np.where(np.arange(len(a)) >= at, cmath.exp(1j * math.pi / 4), 1)


def test_pilots_undo_a_slip_after_the_window() -> None:
    a = _psk8(5, 60)
    x = _jump(a, 10)
    kw: dict[str, Any] = {"decision": "psk8", "phase_loop_gains": (0.0, 0.0)}
    plain = sf.dfe_equalizer(x, a[:10], 1, 0, 0.0, **kw)
    assert np.allclose(plain.symbols[10:], x[10:], atol=1e-15)  # nothing sees the turn
    pilots = a[10 + 4 :: 5]  # outputs 14, 19, ...
    r = sf.dfe_equalizer(x, a[:10], 1, 0, 0.0, pilots=pilots, pilot_interval=5, **kw)
    # window 2: corrected after the second pilot, output 19
    assert np.allclose(r.symbols[:20], x[:20], atol=1e-15)
    assert np.allclose(r.symbols[20:], a[20:], atol=1e-14)
    r1 = sf.dfe_equalizer(
        x, a[:10], 1, 0, 0.0, pilots=pilots, pilot_interval=5, slip_window=1, **kw
    )
    assert np.allclose(r1.symbols[15:], a[15:], atol=1e-14)


def test_a_pilot_is_the_reference_there() -> None:
    a = _psk8(6, 40)
    x = _jump(a, 8)
    pilots = a[8 + 2 :: 3]
    r = sf.dfe_equalizer(
        x, a[:8], 1, 0, 0.0, decision="psk8", phase_loop_gains=(0.0, 0.0), pilots=pilots,
        pilot_interval=3, slip_window=100,
    )  # fmt: skip
    # with no correction yet, the error at a pilot is against the pilot, not the decision
    assert abs(r.errors[10] - (a[10] - x[10])) < 1e-15
    assert abs(r.errors[9]) < 1e-15


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"pilots": [1, 1j, -1]}, "go together"),
        ({"pilot_interval": 1}, "go together"),
        ({"pilots": [1, 1j], "pilot_interval": 1}, "pilots"),
        ({"pilots": [1, 1j, -1], "pilot_interval": 0}, "pilot_interval"),
        ({"pilots": [1, 1j, -1], "pilot_interval": 1, "slip_window": 0}, "slip_window"),
        ({"pilots": [1, 1j, -1], "pilot_interval": 1, "phase_loop_gains": None}, "phase_loop"),
        ({"pilots": [1, math.nan, -1], "pilot_interval": 1}, "pilots"),
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    base: dict[str, Any] = {
        "samples": [1, 1j, -1, -1j],
        "training": [1],
        "num_taps": 3,
        "num_feedback": 0,
        "step": 0.5,
        "decision": "qpsk",
        "phase_loop_gains": (0.1, 0.0),
    }
    with pytest.raises(ValueError, match=match):
        sf.dfe_equalizer(**{**base, **kw})


def _link(**kw: Any) -> QpskLinkConfig:
    base: dict[str, Any] = {
        "modulation": "psk8",
        "num_symbols": 6000,
        "preamble_symbols": 100,
        "eb_n0_db": 12.0,
        "frequency_offset_hz": 5.0,
        "multipath_delays": (0, 4),
        "multipath_gains": ((1.0, 0.0), (0.9, 0.0)),
        "equalizer_taps": 11,
        "equalizer_feedback": 2,
        "equalizer_start": "least_squares",
        "equalizer_loop_gains": (0.01, 0.0001),
        "pilot_interval": 20,
        "seed": 80,
    }
    return QpskLinkConfig(**{**base, **kw})


def test_link_pilots_catch_the_slips() -> None:
    # measured in ADR 0075: 0.0012-0.0099 with pilots; 6 of 10 slip to 0.32-0.63 without
    with_p = [qpsk_link(_link(seed=s)).bit_errors.rate for s in range(80, 90)]
    without = [qpsk_link(_link(seed=s, pilot_interval=None)).bit_errors.rate for s in range(80, 90)]
    assert max(with_p) < 0.015
    assert max(without) > 0.1


def test_link_pilots_do_not_count() -> None:
    c = _link(modulation="qpsk", eb_n0_db=None, num_symbols=1000, pilot_interval=7)
    r = qpsk_link(c)
    pilots = (1000 - 100) // 7
    assert r.bit_errors.compared == 2 * (1000 - 100 - pilots)
    assert r.bit_errors.rate < 0.01  # the loop settling in, not the pilots
    assert qpsk_link(dataclasses.replace(c, pilot_interval=None)).bit_errors.compared == 2 * 900


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"pilot_interval": 0}, "pilot_interval"),
        ({"equalizer_loop_gains": None}, "pilot_interval needs"),
    ],
)
def test_link_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        qpsk_link(_link(**kw))


def test_report_json_carries_the_interval() -> None:
    c = qpsk_link(_link(num_symbols=600, eb_n0_db=None)).to_dict()["config"]
    assert c["pilot_interval"] == 20
