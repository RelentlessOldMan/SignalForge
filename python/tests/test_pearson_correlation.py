"""Pearson correlation (ADR 0371)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_numpy() -> None:
    rng = np.random.default_rng(83)
    a = rng.standard_normal(500)
    b = 0.3 * a + rng.standard_normal(500)
    assert sf.pearson_correlation(a, b) == pytest.approx(np.corrcoef(a, b)[0, 1], rel=1e-12)


def test_is_unchanged_by_scale_and_offset() -> None:
    rng = np.random.default_rng(84)
    a, b = rng.standard_normal(40), rng.standard_normal(40)
    got = sf.pearson_correlation(3 * a - 1, 0.5 * b + 9)
    assert got == pytest.approx(sf.pearson_correlation(a, b), rel=1e-12)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.pearson_correlation([1.0, 2.0, 3.0], [4.0, 4.0, 4.0])
