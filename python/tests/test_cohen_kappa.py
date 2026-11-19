"""Cohen's kappa (ADR 0383)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_fleiss_kappa_form_for_equal_marginals() -> None:
    # With both raters using each label equally often, Cohen's and Fleiss' chance terms agree.
    a = np.array([0.0, 0.0, 1.0, 1.0, 2.0, 2.0])
    b = np.array([0.0, 1.0, 1.0, 2.0, 2.0, 0.0])
    counts = np.stack([(a == c).astype(float) + (b == c) for c in range(3)], axis=1)
    assert sf.cohen_kappa(a, b) == pytest.approx(sf.fleiss_kappa(counts), abs=1e-14)


def test_is_symmetric() -> None:
    rng = np.random.default_rng(111)
    a = rng.integers(0, 4, 100).astype(float)
    b = np.where(rng.random(100) < 0.5, a, rng.integers(0, 4, 100))
    assert sf.cohen_kappa(a, b) == sf.cohen_kappa(b, a)


def test_rejects_one_shared_label() -> None:
    with pytest.raises(ValueError):
        sf.cohen_kappa([1.0, 1.0], [1.0, 1.0])
