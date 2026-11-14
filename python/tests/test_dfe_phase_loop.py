"""The phase loop inside the decision-feedback equalizer (conventions: Synchronization,
Decision-feedback equalizer; ADR 0073)."""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

H = np.array([1, 0.5 - 0.25j, -0.2 + 0.15j, 0.1])


def _turning(seed: int, n: int, rate: float, sigma: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * n).astype(np.uint8))
    x = np.convolve(a, H)[:n] * np.exp(1j * rate * np.arange(n))
    x = x + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return a, x


def test_zero_gains_are_no_loop_exactly() -> None:
    a, x = _turning(1, 300, 0.01)
    plain = sf.dfe_equalizer(x, a[:40], 5, 3, 0.1, decision="qpsk")
    zero = sf.dfe_equalizer(x, a[:40], 5, 3, 0.1, decision="qpsk", phase_loop_gains=(0.0, 0.0))
    np.testing.assert_array_equal(zero.symbols, plain.symbols)
    np.testing.assert_array_equal(zero.taps, plain.taps)
    np.testing.assert_array_equal(zero.feedback_taps, plain.feedback_taps)


def test_follows_a_frequency_the_taps_cannot() -> None:
    # 0.01 rad per symbol: a type-2 loop takes the ramp out with no steady-state phase error
    a, x = _turning(2, 3000, 0.01, sigma=0.05)
    kw: dict[str, Any] = {"decision": "qpsk"}
    plain = sf.dfe_equalizer(x, a[:100], 5, 3, 0.1, **kw)
    loop = sf.dfe_equalizer(x, a[:100], 5, 3, 0.1, phase_loop_gains=(0.05, 0.001), **kw)
    mse = [float(np.mean(np.abs(r.symbols[2000:] - a[2000:]) ** 2)) for r in (plain, loop)]
    assert mse[1] < 0.02 < 0.1 < mse[0]
    # the forward taps stay in their own frame: the main tap is near 1, not turned
    assert abs(loop.taps[2] - 1) < 0.2


def test_constant_phase_is_taken_out_by_the_loop_not_the_taps() -> None:
    a, x = _turning(3, 2000, 0.0)
    x = x * np.exp(0.6j)
    plain = sf.dfe_equalizer(x, a, 5, 3, 0.1)
    loop = sf.dfe_equalizer(x, a, 5, 3, 0.1, phase_loop_gains=(0.05, 0.001))
    for r in (plain, loop):
        assert float(np.mean(np.abs(r.symbols[1500:] - a[1500:]) ** 2)) < 2e-3
    # without the loop the main tap turns by -0.6 rad; with it the loop does and the tap stays put
    assert abs(np.angle(plain.taps[2]) + 0.6) < 0.05
    assert abs(np.angle(loop.taps[2])) < 0.05


@pytest.mark.parametrize(
    ("gains", "match"),
    [((0.1, -0.01), "negative"), ((math.nan, 0.0), "finite"), ((0.1,), "pair")],
)
def test_rejects(gains: Any, match: str) -> None:
    x = np.ones(4, dtype=np.complex128)
    with pytest.raises(ValueError, match=match):
        sf.dfe_equalizer(x, x, 3, 1, 0.5, phase_loop_gains=gains)


ECHO = {"multipath_delays": (0, 4), "multipath_gains": ((1.0, 0.0), (0.9, 0.0))}


def _link(**kw: Any) -> QpskLinkConfig:
    base: dict[str, Any] = {
        "num_symbols": 6000,
        "preamble_symbols": 100,
        "eb_n0_db": 8.0,
        "frequency_offset_hz": 5.0,
        "equalizer_taps": 11,
        "equalizer_feedback": 2,
        "equalizer_start": "least_squares",
        "equalizer_loop_gains": (0.02, 0.0001),
        "seed": 80,
        **ECHO,
    }
    return QpskLinkConfig(**{**base, **kw})


@pytest.mark.parametrize(("mod", "eb"), [("qpsk", 8.0), ("qam16", 14.0), ("psk8", 12.0)])
def test_link_short_preamble_decodes_with_the_loop(mod: str, eb: float) -> None:
    # measured in ADR 0073: seed 80 at 0.0007, 0.0006, 0.001 with the loop; 0.48-0.51 without
    # it for QPSK and 8-PSK
    assert qpsk_link(_link(modulation=mod, eb_n0_db=eb)).bit_errors.rate < 0.003


def test_link_noiseless_short_preamble_needs_the_loop() -> None:
    # no noise, so the same in every language: the frequency is about 0.1 Hz off
    c = _link(modulation="qam16", eb_n0_db=None)
    assert qpsk_link(c).bit_errors.errors == 0
    assert qpsk_link(dataclasses.replace(c, equalizer_loop_gains=None)).bit_errors.rate > 0.1


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"equalizer_loop_gains": (0.1, -1.0)}, "equalizer_loop_gains"),
        ({"equalizer_loop_gains": (0.1,)}, "equalizer_loop_gains"),
        (
            {
                "equalizer_taps": None,
                "equalizer_feedback": 0,
                "equalizer_start": "impulse",
                **{k: None for k in ECHO},
            },
            "equalizer_loop_gains needs",
        ),
    ],
)
def test_link_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        qpsk_link(_link(**kw))


def test_report_json_carries_the_gains() -> None:
    c = qpsk_link(_link(num_symbols=600, eb_n0_db=None)).to_dict()["config"]
    assert list(c["equalizer_loop_gains"]) == [0.02, 0.0001]
