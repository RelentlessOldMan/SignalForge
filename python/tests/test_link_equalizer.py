"""The LMS equalizer in the single-carrier link (conventions: QPSK link; ADR 0067)."""

from __future__ import annotations

import math
from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

DELAYS = (0, 2, 5)
GAINS = ((1.0, 0.0), (0.3, 0.2), (-0.1, 0.0))
ALLOWANCE_DB = 1.0  # noise enhancement and misadjustment: a test allowance, not derived
THEORY = {
    "qpsk": sf.qpsk_ber_theory,
    "qam16": sf.qam16_ber_theory,
    "psk8": sf.psk8_ber_theory,
    "qam64": sf.qam64_ber_theory,
}
BITS = {"qpsk": 2, "qam16": 4, "psk8": 3, "qam64": 6}


def _eq(**kw: Any) -> QpskLinkConfig:
    base = {
        "num_symbols": 4000,
        "preamble_symbols": 500,
        "phase_block_symbols": 64,
        "delay_samples": 3,
        "frequency_offset_hz": 5.0,
        "phase": 0.7,
        "equalizer_taps": 11,
        "multipath_delays": DELAYS,
        "multipath_gains": GAINS,
    }
    return QpskLinkConfig(**{**base, **kw})


def _rho(t: float, beta: float) -> float:
    """The raised cosine at t symbols, written out (no edge point is used here)."""
    sinc = 1.0 if t == 0 else math.sin(math.pi * t) / (math.pi * t)
    return sinc * math.cos(math.pi * beta * t) / (1 - (2 * beta * t) ** 2)


@pytest.mark.parametrize("mod", sorted(BITS))
def test_noiseless_multipath_is_recovered(mod: str) -> None:
    r = qpsk_link(_eq(modulation=mod))
    assert r.bit_errors.errors == 0
    assert r.bit_errors.compared == BITS[mod] * (4000 - 500)  # the preamble does not count
    assert r.evm is not None and r.evm.num_symbols == 3500 and r.evm.rms < 0.03
    assert r.ber_theory is None


@pytest.mark.parametrize("mod", ["qam16", "qam64"])
def test_held_taps_leave_the_echoes(mod: str) -> None:
    # step 0 holds the taps on the chain's own sample, so the echoes stay as interference; with no
    # carrier offset to take out, the flat channel is still clean
    kw = {"modulation": mod, "equalizer_step": 0.0, "frequency_offset_hz": 0.0, "phase": 0.0}
    assert qpsk_link(_eq(**kw)).bit_errors.errors > 0
    flat = qpsk_link(_eq(**kw, multipath_delays=None, multipath_gains=None))
    assert flat.bit_errors.errors == 0
    assert qpsk_link(_eq(modulation=mod)).bit_errors.errors == 0


def test_flat_channel_with_the_equalizer() -> None:
    r = qpsk_link(_eq(multipath_delays=None, multipath_gains=None))
    assert r.bit_errors.errors == 0
    assert r.evm is not None and r.evm.rms < 0.02
    assert r.frame_start == (len(sf.rrc_taps(0.35, 4, 10)) - 1 + 3) // 4


def test_estimates_before_the_equalizer_are_unchanged() -> None:
    # the equalizer only replaces step 7: timing, frame start, frequency and phase are the chain's
    kw = {"multipath_delays": None, "multipath_gains": None}
    with_eq, without = qpsk_link(_eq(**kw)), qpsk_link(_eq(equalizer_taps=None, **kw))
    assert with_eq.timing_offset == without.timing_offset
    assert with_eq.frame_start == without.frame_start
    assert with_eq.frequency_offset_hz == without.frequency_offset_hz
    assert with_eq.phase_offset == without.phase_offset


@pytest.mark.parametrize(
    ("delays", "gains", "e_h"),
    [
        # by hand: one path is a gain, E_h = |g|^2
        ((3,), ((0.6, -0.8),), 1.0),
        ((0,), ((0.5, 0.0),), 0.25),
        # paths a whole symbol (4 samples) apart: rho(1) = 0, so the energies add
        ((0, 4), ((1.0, 0.0), (0.0, 0.5)), 1.25),
        ((0, 8), ((0.8, 0.0), (0.6, 0.0)), 1.0),
        # half a symbol apart: 1 + |g|^2 + 2 Re(g) rho(1/2)
        ((0, 2), ((1.0, 0.0), (0.3, 0.2)), 1 + 0.13 + 2 * 0.3 * _rho(0.5, 0.35)),
    ],
)
def test_ber_theory_is_the_matched_filter_bound(
    delays: tuple[int, ...], gains: tuple[tuple[float, float], ...], e_h: float
) -> None:
    for mod in BITS:
        r = qpsk_link(
            _eq(
                modulation=mod,
                eb_n0_db=7.0,
                num_symbols=600,
                multipath_delays=delays,
                multipath_gains=gains,
            )
        )
        assert r.ber_theory == pytest.approx(THEORY[mod](7.0 + 10 * math.log10(e_h)), rel=1e-12)


def test_ber_theory_without_multipath_is_the_flat_theory() -> None:
    r = qpsk_link(_eq(eb_n0_db=7.0, num_symbols=600, multipath_delays=None, multipath_gains=None))
    assert r.ber_theory == sf.qpsk_ber_theory(7.0)


def test_paths_that_cancel_give_one_half() -> None:
    # two equal paths in antiphase at the same delay: no energy reaches the receiver
    r = qpsk_link(
        _eq(
            eb_n0_db=7.0,
            num_symbols=600,
            multipath_delays=(1, 1),
            multipath_gains=((1.0, 0.0), (-1.0, 0.0)),
        )
    )
    assert r.ber_theory == 0.5


@pytest.mark.parametrize(("mod", "eb"), [("qpsk", 5.0), ("qam16", 10.0)])
def test_ber_between_the_bound_and_the_allowance(mod: str, eb: float) -> None:
    r = qpsk_link(_eq(modulation=mod, eb_n0_db=eb, num_symbols=30000, preamble_symbols=1000))
    assert r.ber_theory is not None
    e_h = 1 + 0.13 + 0.01 + 2 * 0.3 * _rho(0.5, 0.35) - 2 * 0.1 * _rho(1.25, 0.35)
    e_h -= 2 * 0.3 * 0.1 * _rho(0.75, 0.35)
    low = THEORY[mod](eb + 10 * math.log10(e_h))
    assert r.ber_theory == pytest.approx(low, rel=1e-12)
    high = THEORY[mod](eb + 10 * math.log10(e_h) - ALLOWANCE_DB)
    n = r.bit_errors.compared
    sd = math.sqrt(high / n)
    assert low - 4 * sd < r.bit_errors.rate < high + 4 * sd


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"equalizer_taps": 0}, "equalizer_taps"),
        ({"equalizer_taps": -1}, "equalizer_taps"),
        ({"equalizer_step": 2.5}, "equalizer_step"),
        ({"equalizer_step": -0.1}, "equalizer_step"),
        ({"equalizer_step": math.nan}, "equalizer_step"),
        ({"samples_per_symbol": 5}, "even"),
        ({"preamble_symbols": 4000}, "below num_symbols"),
        ({"timing_loop_gains": (0.01, 0.0)}, "loop"),
        ({"carrier_loop_gains": (0.05, 0.001)}, "loop"),
        ({"modulation": "fsk2"}, "single-carrier"),
        ({"modulation": "ofdm"}, "single-carrier"),
        ({"equalizer_taps": None}, "equalizer_taps"),  # multipath in a single-carrier chain
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        qpsk_link(_eq(**kw))


def test_a_bad_step_is_rejected_without_the_equalizer_too() -> None:
    with pytest.raises(ValueError, match="equalizer_step"):
        qpsk_link(QpskLinkConfig(num_symbols=100, equalizer_step=3.0))


def test_report_json_carries_the_equalizer_fields() -> None:
    d = qpsk_link(_eq(num_symbols=600)).to_dict()
    assert d["config"]["equalizer_taps"] == 11
    assert d["config"]["equalizer_step"] == 0.1
