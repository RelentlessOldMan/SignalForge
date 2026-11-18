"""Lempel-Ziv complexity (ADR 0336)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_random_bits_normalize_close_to_one() -> None:
    n = 4000
    b = np.random.default_rng(27).integers(0, 2, n)
    assert sf.lempel_ziv_complexity(b) * math.log2(n) / n == pytest.approx(1.0, abs=0.1)


def test_a_periodic_sequence_stays_small() -> None:
    assert sf.lempel_ziv_complexity([0, 0, 1] * 300) <= 4


def test_rejects_non_bits() -> None:
    with pytest.raises(ValueError):
        sf.lempel_ziv_complexity([0, 1, 3])
