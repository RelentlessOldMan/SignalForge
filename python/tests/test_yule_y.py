"""Yule's Y (ADR 0431)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_maps_onto_yules_q() -> None:
    rng = np.random.default_rng(190)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        y = sf.yule_y(t, d)
        assert sf.yule_q(t, d) == pytest.approx(2 * y / (1 + y * y), rel=1e-13, abs=1e-15)
        assert abs(y) <= abs(sf.yule_q(t, d)) + 1e-15


def test_flipping_one_record_negates_it() -> None:
    rng = np.random.default_rng(191)
    t = (rng.random(30) < 0.5).astype(float)
    d = (rng.random(30) < 0.5).astype(float)
    assert sf.yule_y(t, 1 - d) == -sf.yule_y(t, d)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.yule_y([1.0, 1.0, 1.0], [1.0, 0.0, 1.0])
