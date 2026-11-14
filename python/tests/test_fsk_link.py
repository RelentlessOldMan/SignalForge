"""FSK in the link (conventions: QPSK link, FSK; ADR 0057)."""

from __future__ import annotations

import json

import pytest

from signalforge import QpskLinkConfig, fsk_ber_theory, qpsk_link


@pytest.mark.parametrize("modulation", ["fsk2", "fsk4"])
@pytest.mark.parametrize(("sps", "delay"), [(4, 0), (4, 7), (8, 3), (8, 13), (5, 9)])
def test_noiseless_finds_the_delay(modulation: str, sps: int, delay: int) -> None:
    r = qpsk_link(
        QpskLinkConfig(300, modulation=modulation, samples_per_symbol=sps, delay_samples=delay)
    )
    assert r.timing_offset == delay % sps
    assert r.frame_start == delay // sps
    assert r.bit_errors.errors == 0
    assert r.bit_errors.compared == (300 if modulation == "fsk2" else 600)
    assert r.frequency_offset_hz is None and r.phase_offset is None and r.evm is None
    assert r.ber_theory is None


@pytest.mark.parametrize("modulation", ["fsk2", "fsk4"])
@pytest.mark.parametrize(
    ("df", "phase", "ppm"), [(20.0, 1.0, 0.0), (-35.0, -2.5, 0.0), (0.0, 0.0, 60.0), (10, 3, -60)]
)
def test_noiseless_with_offsets_has_no_errors(
    modulation: str, df: float, phase: float, ppm: float
) -> None:
    # tones a symbol rate apart: a few percent of it costs nothing without noise, and a clock
    # offset that shortens the stream must not move the frame out of the search
    r = qpsk_link(
        QpskLinkConfig(
            500,
            modulation=modulation,
            samples_per_symbol=8,
            frequency_offset_hz=df,
            phase=phase,
            clock_offset_ppm=ppm,
            delay_samples=6,
        )
    )
    assert r.bit_errors.errors == 0
    assert r.frame_start * 8 + r.timing_offset in (6, 7)


def test_fsk2_ber_near_theory() -> None:
    r = qpsk_link(QpskLinkConfig(20000, eb_n0_db=7.0, modulation="fsk2", delay_samples=5, seed=3))
    assert r.ber_theory == fsk_ber_theory(7.0, 2)
    expected = r.ber_theory * r.bit_errors.compared  # about 816; 4 sd is about 14%
    assert 0.85 * expected < r.bit_errors.errors < 1.15 * expected
    # delay 5 or 6: the first sample of a symbol also continues the tone before it
    assert r.frame_start * 4 + r.timing_offset in (5, 6)


def test_fsk4_ber_near_theory() -> None:
    r = qpsk_link(
        QpskLinkConfig(
            20000, eb_n0_db=6.0, modulation="fsk4", delay_samples=2, frequency_offset_hz=8, seed=4
        )
    )
    assert r.ber_theory == fsk_ber_theory(6.0, 4)
    expected = r.ber_theory * r.bit_errors.compared  # about 632; 4 sd is about 16%
    assert 0.82 * expected < r.bit_errors.errors < 1.18 * expected
    assert r.frame_start * 4 + r.timing_offset in (2, 3)


def test_json_has_nulls() -> None:
    d = json.loads(qpsk_link(QpskLinkConfig(64, modulation="fsk4")).to_json())
    assert d["frequency_offset_hz"] is None
    assert d["phase_offset"] is None
    assert d["evm"] is None
    assert d["config"]["modulation"] == "fsk4"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"modulation": "fsk4", "samples_per_symbol": 3},
        {"modulation": "fsk2", "timing_loop_gains": [0.01, 0.0001]},
        {"modulation": "fsk4", "carrier_loop_gains": [0.05, 0.001]},
        {"modulation": "fsk8"},
        {"modulation": "fsk2", "rolloff": 1.5},
    ],
)
def test_rejects(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        qpsk_link(QpskLinkConfig(64, **kwargs))  # type: ignore[arg-type]


def test_unknown_modulation_lists_fsk() -> None:
    with pytest.raises(ValueError, match="fsk2"):
        qpsk_link(QpskLinkConfig(64, modulation="bpsk"))
