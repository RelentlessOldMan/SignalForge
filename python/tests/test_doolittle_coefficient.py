"""The Doolittle coefficient (ADR 0466)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_square_of_the_matthews_correlation() -> None:
    rng = np.random.default_rng(229)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.doolittle_coefficient(t, d)
        assert v == pytest.approx(sf.matthews_correlation(t, d) ** 2, rel=1e-13, abs=1e-15)
        assert v == sf.doolittle_coefficient(d, t)
        assert 0.0 <= v <= 1.0


def test_is_unchanged_when_a_record_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.doolittle_coefficient(1 - t, d) == sf.doolittle_coefficient(t, d)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.doolittle_coefficient([1.0, 0.0], [0.0, 0.0])
