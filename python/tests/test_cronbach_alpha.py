"""Cronbach's alpha (ADR 0380)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_spearman_brown_form_for_parallel_items() -> None:
    # k items sharing a true score of variance 1 with independent errors of variance 1 have
    # inter-item correlation 1/2, so alpha = k r/(1 + (k - 1) r) = 4/5 for k = 4.
    rng = np.random.default_rng(105)
    true = rng.standard_normal(20000)
    rows = true + rng.standard_normal((4, 20000))
    assert sf.cronbach_alpha(rows) == pytest.approx(0.8, abs=0.01)


def test_does_not_change_with_an_offset_per_item() -> None:
    rng = np.random.default_rng(106)
    rows = rng.standard_normal((3, 30))
    shifted = rows + np.array([[5.0], [-2.0], [0.5]])
    assert sf.cronbach_alpha(shifted) == pytest.approx(sf.cronbach_alpha(rows), abs=1e-12)


def test_rejects_ragged_rows() -> None:
    with pytest.raises(ValueError):
        sf.cronbach_alpha([[1.0, 2.0, 3.0], [1.0, 2.0]])
