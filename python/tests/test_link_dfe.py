"""Decision feedback and the preamble frequency in the link (conventions: QPSK link, Receiver,
step 7; ADR 0070)."""

from __future__ import annotations

import math
from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

# an echo of 0.9 one symbol late: a notch 20 dB deep at half the symbol rate
ECHO = {"multipath_delays": (0, 4), "multipath_gains": ((1.0, 0.0), (0.9, 0.0))}


def _dfe(**kw: Any) -> QpskLinkConfig:
    base: dict[str, Any] = {
        "num_symbols": 4000,
        "preamble_symbols": 1000,
        "delay_samples": 3,
        "frequency_offset_hz": 5.0,
        "phase": 0.7,
        "equalizer_taps": 11,
        "equalizer_feedback": 2,
        **ECHO,
    }
    return QpskLinkConfig(**{**base, **kw})


@pytest.mark.parametrize(
    ("mod", "pre"), [("qpsk", 1000), ("qam16", 1000), ("psk8", 1000), ("qam64", 2000)]
)
def test_noiseless_echo_is_recovered_with_feedback(mod: str, pre: int) -> None:
    # 64-QAM's decisions need the taps nearer convergence than training on 1000 symbols leaves
    r = qpsk_link(_dfe(modulation=mod, preamble_symbols=pre))
    assert r.bit_errors.errors == 0
    assert r.evm is not None and r.evm.rms < 0.08


@pytest.mark.parametrize("mod", ["qam16", "psk8", "qam64"])
def test_the_linear_equalizer_cannot_span_the_echo(mod: str) -> None:
    # its inverse decays as 0.9^k, longer than 11 taps at half a symbol reach
    assert qpsk_link(_dfe(modulation=mod, equalizer_feedback=0)).bit_errors.errors > 0


def test_preamble_frequency_through_the_echo() -> None:
    # the blind QPSK estimate is about 1 Hz off through this echo at 8 dB (ADR 0070)
    for seed in range(5):
        r = qpsk_link(_dfe(eb_n0_db=8.0, seed=seed))
        assert r.frequency_offset_hz is not None
        assert abs(r.frequency_offset_hz - 5.0) < 0.1  # a test allowance, not derived


def test_noiseless_flat_preamble_frequency() -> None:
    kw = {"multipath_delays": None, "multipath_gains": None, "equalizer_feedback": 0}
    with_eq, without = qpsk_link(_dfe(**kw)), qpsk_link(_dfe(equalizer_taps=None, **kw))
    assert with_eq.frequency_offset_hz == pytest.approx(5.0, abs=1e-3)
    assert with_eq.timing_offset == without.timing_offset
    assert with_eq.frame_start == without.frame_start
    assert with_eq.phase_offset == pytest.approx(
        without.phase_offset, abs=1e-6
    )  # f₁ differs (ADR 0071)


def test_fewer_than_two_full_blocks_keep_the_chain_frequency() -> None:
    # P = 40 and B = 32 leave one full block: steps 2-6 give the frequency, from the data-aided f1
    flat = {"multipath_delays": None, "multipath_gains": None}
    r = qpsk_link(_dfe(preamble_symbols=40, **flat))
    assert r.frequency_offset_hz == pytest.approx(5.0, abs=1e-5)  # a test allowance, not derived


def test_one_preamble_symbol_keeps_the_blind_estimate() -> None:
    # no symbol-to-symbol step to correlate: f1 is the blind estimate (ADR 0071)
    kw = {"preamble_symbols": 1, "multipath_delays": None, "multipath_gains": None}
    with_eq = qpsk_link(_dfe(**kw))
    without = qpsk_link(_dfe(equalizer_taps=None, equalizer_feedback=0, **kw))
    assert with_eq.frequency_offset_hz == without.frequency_offset_hz


def test_data_aided_coarse_frequency_for_8psk() -> None:
    # the 8th-power estimate is 31.25 Hz off here without the preamble (ADR 0071)
    for seed, f0 in ((71, 5.0), (72, 37.0), (73, -120.0)):
        kw = {"modulation": "psk8", "eb_n0_db": 12.0, "num_symbols": 20000, "seed": seed}
        r = qpsk_link(_dfe(frequency_offset_hz=f0, **kw))
        assert r.frequency_offset_hz is not None
        assert abs(r.frequency_offset_hz - f0) < 0.05  # a test allowance, not derived
        assert r.bit_errors.rate < 0.002  # measured 0.0002-0.0011 over four seeds (ADR 0071)


@pytest.mark.parametrize(("mod", "eb"), [("qpsk", 8.0), ("qam16", 14.0)])
def test_feedback_beats_the_linear_equalizer_above_the_bound(mod: str, eb: float) -> None:
    kw = {"modulation": mod, "eb_n0_db": eb, "num_symbols": 20000, "seed": 70}
    dfe, lms = qpsk_link(_dfe(**kw)), qpsk_link(_dfe(equalizer_feedback=0, **kw))
    e_h = 1 + 0.81  # paths a whole symbol apart: rho(1) = 0, so the energies add
    bound = {"qpsk": sf.qpsk_ber_theory, "qam16": sf.qam16_ber_theory}[mod](
        eb + 10 * math.log10(e_h)
    )
    assert dfe.ber_theory == pytest.approx(bound, rel=1e-12)
    assert bound < dfe.bit_errors.rate < lms.bit_errors.rate / 10


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"equalizer_feedback": -1}, "equalizer_feedback"),
        ({"equalizer_taps": None, **{k: None for k in ECHO}}, "equalizer_feedback needs"),
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        qpsk_link(_dfe(**kw))


def test_report_json_carries_the_feedback_count() -> None:
    assert qpsk_link(_dfe(num_symbols=1200)).to_dict()["config"]["equalizer_feedback"] == 2
