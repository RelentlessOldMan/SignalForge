"""Tarwid's coefficient (ADR 0453)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_from_minus_one_to_below_one() -> None:
    rng = np.random.default_rng(216)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = d[1] = 1.0
        v = sf.tarwid_coefficient(t, d)
        assert -1.0 <= v < 1.0
        assert v == sf.tarwid_coefficient(d, t)


def test_has_the_sign_of_the_covariance() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
    d = [1.0, 1.0, 0.0, 1.0, 0.0, 0.0]
    assert sf.tarwid_coefficient(t, d) > 0
    assert sf.tarwid_coefficient(t, [1.0 - v for v in d]) < 0


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.tarwid_coefficient([0.0, 0.0], [0.0, 1.0])
