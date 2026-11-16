"""Speech transmission index (conventions: Speech transmission index; ADR 0177)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

F_MOD = 10 ** (np.arange(-2, 12) / 10)


def test_a_long_reverberation_lowers_the_sti() -> None:
    fs = 8000.0
    sti = []
    for t60 in (0.5, 2.0):
        r = 10 ** (-3 / (t60 * fs))
        m = sf.modulation_transfer(r ** np.arange(int(3 * t60 * fs)), fs, F_MOD)
        sti.append(sf.speech_transmission_index(np.tile(m, (7, 1))))
    assert 0 < sti[1] < sti[0] < 1


def test_a_uniform_mtf_gives_its_transmission_index() -> None:
    m = 0.7
    expected = (10 * math.log10(m / (1 - m)) + 15) / 30
    assert sf.speech_transmission_index(np.full((7, 14), m)) == pytest.approx(expected, abs=1e-14)


def test_a_ragged_matrix_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.speech_transmission_index([[0.5, 0.5]] * 6 + [[0.5]])
