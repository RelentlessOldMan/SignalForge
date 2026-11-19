"""Buishand range test (ADR 0367)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_finds_a_level_shift() -> None:
    rng = np.random.default_rng(75)
    x = rng.standard_normal(400)
    x[250:] += 1.0
    got = sf.buishand_range(x)
    assert 235 <= got.index <= 265
    assert got.q > 5


def test_is_unchanged_by_scale_and_offset() -> None:
    x = np.random.default_rng(76).standard_normal(64)
    a = sf.buishand_range(x)
    b = sf.buishand_range(4.0 * x + 7.0)
    assert b.q == pytest.approx(a.q, rel=1e-12) and b.r == pytest.approx(a.r, rel=1e-12)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.buishand_range([1.0, 1.0])
