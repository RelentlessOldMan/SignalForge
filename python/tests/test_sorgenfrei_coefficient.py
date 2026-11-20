"""The Sorgenfrei coefficient (ADR 0434)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_square_of_the_sorgenfrei_coefficient() -> None:
    rng = np.random.default_rng(195)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        o = sf.ochiai_coefficient(t, d)
        assert sf.sorgenfrei_coefficient(t, d) == pytest.approx(o * o, rel=1e-14)


def test_is_recall_times_precision() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    tp = float(np.sum(t * d))
    want = (tp / np.sum(t)) * (tp / np.sum(d))
    assert sf.sorgenfrei_coefficient(t, d) == pytest.approx(want, rel=1e-15)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.sorgenfrei_coefficient([1.0, 0.0], [0.0, 0.0])
