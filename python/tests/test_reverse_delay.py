"""Reverse delay (ADR 0298)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_each_block_is_the_previous_one_reversed() -> None:
    rng = np.random.default_rng(298)
    x = rng.standard_normal(1000)
    y = sf.reverse_delay(x, 100, 1.0)
    assert np.all(y[:100] == 0.0)
    for q in range(1, 10):
        assert np.array_equal(y[q * 100 : (q + 1) * 100], x[(q - 1) * 100 : q * 100][::-1])


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.reverse_delay([1j], 2, 0.5)
