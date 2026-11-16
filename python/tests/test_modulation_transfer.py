"""Modulation transfer function (conventions: Modulation transfer function; ADR 0176)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_a_long_decay_matches_schroeders_continuous_form() -> None:
    fs, t60 = 8000.0, 1.0
    r = 10 ** (-3 / (t60 * fs))
    ir = r ** np.arange(int(3 * fs))
    f = np.array([0.63, 2.0, 8.0])
    expected = 1 / np.sqrt(1 + (2 * math.pi * f * t60 / (6 * math.log(10))) ** 2)
    assert sf.modulation_transfer(ir, fs, f) == pytest.approx(expected, rel=1e-3)
