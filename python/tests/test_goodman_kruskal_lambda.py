"""Goodman and Kruskal's lambda (ADR 0447)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_anderbergs_d_over_its_largest_value() -> None:
    rng = np.random.default_rng(210)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        nt, nd = t.sum(), d.sum()
        base = max(nt, 25 - nt) + max(nd, 25 - nd)
        v = sf.goodman_kruskal_lambda(t, d)
        assert 0.0 <= v <= 1.0
        assert v == pytest.approx(sf.anderberg_d(t, d) * 50 / (50 - base), rel=1e-14, abs=1e-15)


def test_is_unchanged_when_a_record_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    assert sf.goodman_kruskal_lambda(t, 1 - d) == sf.goodman_kruskal_lambda(t, d)
    assert sf.goodman_kruskal_lambda(d, t) == sf.goodman_kruskal_lambda(t, d)


def test_rejects_two_constant_records() -> None:
    with pytest.raises(ValueError):
        sf.goodman_kruskal_lambda([1.0, 1.0], [0.0, 0.0])
