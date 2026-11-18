"""Transient shaper (ADR 0281)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_amount_zero_and_equal_envelopes_give_the_input() -> None:
    rng = np.random.default_rng(50)
    x = rng.standard_normal(200)
    assert np.array_equal(sf.transient_shaper(x, 0.2, 0.9, 0.0), x)
    assert np.array_equal(sf.transient_shaper(x, 0.6, 0.6, 3.0), x)


def test_onset_is_raised_and_sustain_left_alone() -> None:
    x = np.concatenate([np.zeros(10), np.ones(2000)])
    y = np.real(sf.transient_shaper(x, 0.5, 0.99, 1.0))
    assert y[10] > 10
    assert y[-1] == pytest.approx(1.0, abs=1e-6)


def test_rejects_fast_of_one() -> None:
    with pytest.raises(ValueError):
        sf.transient_shaper([1.0], 1.0, 0.5, 1.0)
