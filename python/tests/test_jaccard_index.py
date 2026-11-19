"""The Jaccard index (ADR 0388)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_gives_the_f1_score_through_2j_over_1_plus_j() -> None:
    rng = np.random.default_rng(117)
    truth = (rng.random(300) < 0.3).astype(float)
    decision = np.where(rng.random(300) < 0.8, truth, 1 - truth)
    j = sf.jaccard_index(truth, decision)
    assert 2 * j / (1 + j) == pytest.approx(sf.f1_score(truth, decision), abs=1e-15)


def test_is_symmetric() -> None:
    a = [1.0, 1.0, 0.0, 1.0, 0.0]
    b = [0.0, 1.0, 1.0, 1.0, 0.0]
    assert sf.jaccard_index(a, b) == sf.jaccard_index(b, a)


def test_rejects_an_empty_union() -> None:
    with pytest.raises(ValueError):
        sf.jaccard_index([0.0, 0.0], [0.0, 0.0])
