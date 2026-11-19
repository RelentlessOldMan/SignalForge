"""Cosine similarity entropy (ADR 0358)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_ignores_amplitude() -> None:
    x = np.random.default_rng(67).standard_normal(200)
    assert sf.cosine_similarity_entropy(3.5 * x, 2, 0.3) == sf.cosine_similarity_entropy(x, 2, 0.3)


def test_signs_by_hand() -> None:
    assert sf.cosine_similarity_entropy([1.0, 2.0, -1.0, 3.0], 1, 0.5) == 1.0


def test_rejects_a_zero_vector() -> None:
    with pytest.raises(ValueError):
        sf.cosine_similarity_entropy([1.0, 0.0, 0.0, 2.0], 2, 0.5)
