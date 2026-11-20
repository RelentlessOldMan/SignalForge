"""The Forbes coefficient (ADR 0435)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_observed_over_the_expected_overlap() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    expected = np.sum(t) * np.sum(d) / t.size
    want = float(np.sum(t * d) / expected)
    assert sf.forbes_coefficient(t, d) == pytest.approx(want, rel=1e-15)


def test_is_symmetric() -> None:
    rng = np.random.default_rng(196)
    t = (rng.random(30) < 0.4).astype(float)
    d = (rng.random(30) < 0.5).astype(float)
    t[0] = d[1] = 1.0
    assert sf.forbes_coefficient(t, d) == sf.forbes_coefficient(d, t)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.forbes_coefficient([1.0, 0.0], [0.0, 0.0])
