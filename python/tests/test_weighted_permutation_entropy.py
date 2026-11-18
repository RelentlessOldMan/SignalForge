"""Weighted permutation entropy (ADR 0343)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_equal_weights_match_permutation_entropy() -> None:
    # A +-1 square-ish pattern where every window has the same variance.
    x = np.array([0.0, 1.0] * 20)
    assert sf.weighted_permutation_entropy(x, 2) == pytest.approx(sf.permutation_entropy(x, 2))


def test_quiet_noise_counts_for_little() -> None:
    rng = np.random.default_rng(41)
    x = np.sin(2 * np.pi * np.arange(2000) / 100)
    noisy = x + 1e-3 * rng.standard_normal(2000)
    assert sf.weighted_permutation_entropy(noisy, 3) < sf.permutation_entropy(noisy, 3)


def test_scale_changes_nothing() -> None:
    x = np.random.default_rng(42).standard_normal(300)
    assert sf.weighted_permutation_entropy(5 * x, 4) == pytest.approx(
        sf.weighted_permutation_entropy(x, 4), rel=1e-12
    )


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.weighted_permutation_entropy(np.ones(10), 3)
