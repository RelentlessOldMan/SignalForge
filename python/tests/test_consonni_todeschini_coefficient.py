"""The Consonni-Todeschini coefficient (ADR 0457)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_simple_matching_on_a_log_scale() -> None:
    rng = np.random.default_rng(220)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.consonni_todeschini_coefficient(t, d)
        s = sf.simple_matching_coefficient(t, d)
        assert v == pytest.approx(math.log1p(25 * s) / math.log1p(25), rel=1e-14)
        assert s <= v + 1e-15
        assert v == sf.consonni_todeschini_coefficient(d, t)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    want = sf.consonni_todeschini_coefficient(t, d)
    assert sf.consonni_todeschini_coefficient(1 - t, 1 - d) == want


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.consonni_todeschini_coefficient([1.0, 0.0], [1.0])
