"""The simple matching coefficient (ADR 0424)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_minus_the_bit_error_ratio() -> None:
    rng = np.random.default_rng(183)
    bits = rng.integers(0, 2, 200).astype(float)
    rx = bits.copy()
    rx[[5, 40, 41, 150]] = 1.0 - rx[[5, 40, 41, 150]]
    assert sf.simple_matching_coefficient(bits, rx) == pytest.approx(1 - 4 / 200, rel=1e-15)


def test_is_symmetric() -> None:
    t, d = [1.0, 1.0, 0.0, 1.0], [0.0, 1.0, 1.0, 1.0]
    assert sf.simple_matching_coefficient(t, d) == sf.simple_matching_coefficient(d, t)


def test_rejects_a_value_other_than_zero_or_one() -> None:
    with pytest.raises(ValueError):
        sf.simple_matching_coefficient([1.0, 0.5], [1.0, 0.0])
