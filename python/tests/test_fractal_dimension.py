"""Katz and Petrosian fractal dimensions (ADRs 0334, 0335)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_katz_of_a_line_is_one() -> None:
    assert sf.katz_dimension(np.linspace(0, 5, 50)) == pytest.approx(1.0, abs=1e-14)


def test_katz_grows_with_irregularity() -> None:
    rng = np.random.default_rng(26)
    smooth = np.sin(2 * np.pi * np.arange(500) / 200)
    assert sf.katz_dimension(smooth) < sf.katz_dimension(rng.standard_normal(500))


def test_katz_rejects_a_zero_denominator() -> None:
    with pytest.raises(ValueError):
        sf.katz_dimension([0.0, 3.0, 0.0])


def test_petrosian_by_hand() -> None:
    # 0, 2, 1, 3: steps +, -, +: two changes.
    n = 4
    expected = math.log10(n) / (math.log10(n) + math.log10(n / (n + 0.8)))
    assert sf.petrosian_dimension([0.0, 2.0, 1.0, 3.0]) == pytest.approx(expected, rel=1e-15)


def test_petrosian_rejects_two_samples() -> None:
    with pytest.raises(ValueError):
        sf.petrosian_dimension([0.0, 1.0])
