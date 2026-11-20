"""Digby's H (ADR 0444)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_lies_between_yules_y_and_yules_q() -> None:
    rng = np.random.default_rng(207)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        y, q = sf.yule_y(t, d), sf.yule_q(t, d)
        h = sf.digby_h(t, d)
        assert min(y, q) - 1e-15 <= h <= max(y, q) + 1e-15


def test_changes_sign_when_the_decision_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0])
    d = np.array([1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    assert sf.digby_h(t, 1 - d) == pytest.approx(-sf.digby_h(t, d), rel=1e-15)


def test_rejects_a_table_with_both_products_zero() -> None:
    with pytest.raises(ValueError):
        sf.digby_h([1.0, 1.0, 1.0], [1.0, 0.0, 1.0])
