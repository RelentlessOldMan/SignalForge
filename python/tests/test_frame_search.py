"""The frame search in blocks (conventions: QPSK link, Receiver, step 3; ADR 0068)."""

from __future__ import annotations

from typing import Any

import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

L = len(sf.rrc_taps(0.35, 4, 10))
# strong inter-symbol interference: the coarse QPSK frequency estimate is about 1.3 Hz off
STRONG: dict[str, Any] = {
    "multipath_delays": (0, 3, 7),
    "multipath_gains": ((1.0, 0.0), (0.4, -0.3), (-0.2, 0.1)),
    "equalizer_taps": 11,
}


def test_a_long_preamble_finds_the_frame_through_a_frequency_error() -> None:
    # a 1000-symbol preamble is one second at 1 kHz; coherently over it, a 1 Hz residual turns
    # the correlation a full cycle (ADR 0068)
    for seed in range(10):
        c = QpskLinkConfig(
            num_symbols=6000, preamble_symbols=1000, eb_n0_db=6.0, seed=seed, **STRONG
        )
        assert qpsk_link(c).frame_start == (L - 1) // 4


@pytest.mark.parametrize(("pre", "blk", "delay"), [(200, 32, 7), (100, 7, 13), (33, 32, 2)])
def test_noiseless_blocks_find_the_true_start(pre: int, blk: int, delay: int) -> None:
    r = qpsk_link(
        QpskLinkConfig(
            num_symbols=600,
            preamble_symbols=pre,
            phase_block_symbols=blk,
            delay_samples=delay,
            frequency_offset_hz=30.0,
            phase=-2.0,
        )
    )
    assert r.frame_start == (L - 1 + delay) // 4
    assert r.bit_errors.errors == 0
