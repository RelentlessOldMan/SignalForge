"""The ROC AUC (ADR 0393)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_share_of_pairs_ranked_right() -> None:
    rng = np.random.default_rng(125)
    truth = (rng.random(150) < 0.4).astype(float)
    score = np.round(rng.normal(truth, 1.0), 1)
    p, q = score[truth == 1][:, None], score[truth == 0][None, :]
    expected = np.mean((p > q) + 0.5 * (p == q))
    assert sf.roc_auc(truth, score) == pytest.approx(expected, abs=1e-15)


def test_is_unchanged_by_a_monotone_map_of_the_score() -> None:
    rng = np.random.default_rng(126)
    truth = (rng.random(100) < 0.5).astype(float)
    score = rng.normal(truth, 1.0)
    assert sf.roc_auc(truth, np.exp(score)) == sf.roc_auc(truth, score)


def test_rejects_a_missing_class() -> None:
    with pytest.raises(ValueError):
        sf.roc_auc([1.0, 1.0], [0.2, 0.4])
