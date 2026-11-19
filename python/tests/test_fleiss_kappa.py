"""Fleiss' kappa (ADR 0382)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_near_zero_for_raters_choosing_at_random() -> None:
    rng = np.random.default_rng(109)
    labels = rng.integers(0, 3, (4000, 5))
    counts = np.stack([np.sum(labels == c, axis=1) for c in range(3)], axis=1)
    assert sf.fleiss_kappa(counts) == pytest.approx(0.0, abs=0.02)


def test_does_not_depend_on_the_order_of_the_categories() -> None:
    rng = np.random.default_rng(110)
    counts = rng.multinomial(7, [0.5, 0.3, 0.2], 40)
    assert sf.fleiss_kappa(counts[:, ::-1]) == pytest.approx(sf.fleiss_kappa(counts), abs=1e-14)


def test_rejects_ragged_rows() -> None:
    with pytest.raises(ValueError):
        sf.fleiss_kappa([[1.0, 2.0, 0.0], [1.0, 2.0]])
