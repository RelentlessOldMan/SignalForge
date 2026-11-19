"""The Jensen-Shannon divergence (ADR 0408)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_kl_divergence_from_the_mixture() -> None:
    rng = np.random.default_rng(152)
    p, q = rng.uniform(0.1, 1.0, 20), rng.uniform(0.1, 1.0, 20)
    m = (p / p.sum() + q / q.sum()) / 2
    expected = (sf.kl_divergence(p, m) + sf.kl_divergence(q, m)) / 2
    assert sf.js_divergence(p, q) == pytest.approx(expected, rel=1e-12)


def test_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(153)
    p, q = rng.integers(0, 5, 30).astype(float), rng.integers(0, 5, 30).astype(float)
    assert sf.js_divergence(q, p) == pytest.approx(sf.js_divergence(p, q), rel=1e-14)
    assert 0 <= sf.js_divergence(p, q) <= np.log(2)


def test_rejects_unequal_lengths() -> None:
    with pytest.raises(ValueError):
        sf.js_divergence([1.0, 1.0], [1.0])
