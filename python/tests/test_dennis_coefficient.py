"""The Dennis coefficient (ADR 0437)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_follows_from_the_forbes_coefficient() -> None:
    rng = np.random.default_rng(198)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        want = (sf.forbes_coefficient(t, d) - 1) * np.sqrt(np.sum(t) * np.sum(d) / t.size)
        assert sf.dennis_coefficient(t, d) == pytest.approx(want, rel=1e-13, abs=1e-14)


def test_has_the_sign_of_yules_q() -> None:
    rng = np.random.default_rng(199)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        assert np.sign(sf.dennis_coefficient(t, d)) == np.sign(sf.yule_q(t, d))


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.dennis_coefficient([1.0, 0.0], [0.0, 0.0])
