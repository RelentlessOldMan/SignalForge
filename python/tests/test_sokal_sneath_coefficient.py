"""The Sokal-Sneath coefficient (ADR 0427)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_follows_from_the_jaccard_index() -> None:
    rng = np.random.default_rng(186)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = 1.0
        j = sf.jaccard_index(t, d)
        assert sf.sokal_sneath_coefficient(t, d) == pytest.approx(j / (2 - j), rel=1e-14)


def test_is_the_tversky_index_at_two() -> None:
    t, d = [1.0, 1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 1.0, 1.0, 0.0]
    assert sf.sokal_sneath_coefficient(t, d) == pytest.approx(
        sf.tversky_index(t, d, 2.0, 2.0), rel=1e-15
    )


def test_rejects_records_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.sokal_sneath_coefficient([0.0, 0.0], [0.0, 0.0])
