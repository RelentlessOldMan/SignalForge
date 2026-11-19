"""Standard normal homogeneity test (ADR 0368)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_finds_a_level_shift() -> None:
    rng = np.random.default_rng(77)
    x = rng.standard_normal(400)
    x[120:] += 1.0
    got = sf.snht(x)
    assert 105 <= got.index <= 135
    assert got.statistic > 30


def test_matches_the_two_part_form() -> None:
    x = np.random.default_rng(78).standard_normal(50)
    z = (x - x.mean()) / x.std()
    t = [k * z[:k].mean() ** 2 + (50 - k) * z[k:].mean() ** 2 for k in range(1, 50)]
    got = sf.snht(x)
    assert got.statistic == pytest.approx(max(t), rel=1e-10)
    assert got.index == int(np.argmax(t))


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.snht([1.0, 1.0])
