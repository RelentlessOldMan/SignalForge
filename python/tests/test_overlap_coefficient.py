"""The overlap coefficient (ADR 0422)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_at_least_the_jaccard_index() -> None:
    rng = np.random.default_rng(179)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        assert sf.overlap_coefficient(t, d) >= sf.jaccard_index(t, d)


def test_is_symmetric() -> None:
    t, d = [1.0, 1.0, 0.0, 1.0], [0.0, 1.0, 1.0, 1.0]
    assert sf.overlap_coefficient(t, d) == sf.overlap_coefficient(d, t)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.overlap_coefficient([1.0, 0.0], [0.0, 0.0])
