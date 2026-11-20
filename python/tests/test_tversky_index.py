"""The Tversky index (ADR 0423)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def _records(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    t = (rng.random(30) < 0.4).astype(float)
    d = (rng.random(30) < 0.5).astype(float)
    t[0] = d[0] = 1.0
    return t, d


def test_is_the_jaccard_index_at_unit_weights() -> None:
    t, d = _records(180)
    assert sf.tversky_index(t, d, 1.0, 1.0) == pytest.approx(sf.jaccard_index(t, d), rel=1e-15)


def test_is_the_f1_score_at_half_weights() -> None:
    t, d = _records(181)
    tp = float(np.sum((t == 1) & (d == 1)))
    dice = 2 * tp / (np.sum(t) + np.sum(d))
    assert sf.tversky_index(t, d, 0.5, 0.5) == pytest.approx(dice, rel=1e-15)


def test_swapping_records_swaps_weights() -> None:
    t, d = _records(182)
    assert sf.tversky_index(t, d, 0.2, 0.9) == pytest.approx(
        sf.tversky_index(d, t, 0.9, 0.2), rel=1e-15
    )


def test_rejects_a_negative_weight() -> None:
    with pytest.raises(ValueError):
        sf.tversky_index([1.0], [1.0], -1.0, 1.0)
