"""Hurlbert's PIE (ADR 0548)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_drawing_without_replacement() -> None:
    rng = np.random.default_rng(311)
    for n in range(1, 30):
        x = rng.integers(0, 20, n).astype(float)
        x[0] += 2.0
        total = float(np.sum(x))
        p = sf.hurlbert_pie(x)
        same = float(np.sum(x * (x - 1))) / (total * (total - 1))
        assert p == pytest.approx(1 - same, rel=1e-12, abs=1e-14)
        gs = sf.simpson_diversity(x)
        assert p == pytest.approx(gs * total / (total - 1), rel=1e-13, abs=1e-15)
        assert -1e-15 <= p <= 1 + 1e-14
    assert sf.hurlbert_pie([0.0, 9.0]) == 0.0


@pytest.mark.parametrize(
    "bad", [[], [1.0], [0.5, 0.5], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hurlbert_pie(bad)
