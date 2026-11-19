"""The Jeffreys divergence (ADR 0414)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_kl_divergence_both_ways() -> None:
    rng = np.random.default_rng(163)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    both = sf.kl_divergence(p, q) + sf.kl_divergence(q, p)
    assert sf.jeffreys_divergence(p, q) == pytest.approx(both, rel=1e-12)


def test_is_symmetric() -> None:
    rng = np.random.default_rng(164)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    assert sf.jeffreys_divergence(p, q) == pytest.approx(sf.jeffreys_divergence(q, p), rel=1e-14)


def test_rejects_a_zero_in_only_one() -> None:
    with pytest.raises(ValueError):
        sf.jeffreys_divergence([1.0, 0.0], [1.0, 1.0])
