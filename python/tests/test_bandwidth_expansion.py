"""Bandwidth expansion (ADR 0219)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_roots_shrink_by_the_factor() -> None:
    a = sf.reflection_to_lpc([0.6 + 0.2j, -0.4, 0.3j, 0.5])
    before = np.sort_complex(np.roots(a))
    after = np.sort_complex(np.roots(sf.bandwidth_expansion(a, 0.8)))
    assert np.allclose(after, 0.8 * before, atol=1e-10)


def test_real_stays_real() -> None:
    assert sf.bandwidth_expansion([1.0, 0.5], 0.9).dtype == np.float64
