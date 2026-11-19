"""The Rényi divergence (ADR 0413)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_ties_to_the_other_divergences() -> None:
    rng = np.random.default_rng(161)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    half = sf.renyi_divergence(p, q, 0.5)
    assert half == pytest.approx(2 * sf.bhattacharyya_distance(p, q), rel=1e-12)
    two = sf.renyi_divergence(p, q, 2.0)
    assert two == pytest.approx(np.log1p(sf.chi_square_divergence(p, q)), rel=1e-12)


def test_tends_to_the_kl_divergence_and_grows_with_order() -> None:
    rng = np.random.default_rng(162)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    kl = sf.kl_divergence(p, q)
    assert sf.renyi_divergence(p, q, 1.0 + 1e-6) == pytest.approx(kl, rel=1e-5)
    orders = [0.25, 0.5, 0.9, 1.5, 3.0]
    values = [sf.renyi_divergence(p, q, a) for a in orders]
    assert values == sorted(values)


def test_rejects_order_one() -> None:
    with pytest.raises(ValueError):
        sf.renyi_divergence([1.0, 2.0], [2.0, 1.0], 1.0)
