"""The relative risk reduction (ADR 0505)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_minus_the_relative_risk() -> None:
    rng = np.random.default_rng(268)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        v = sf.relative_risk_reduction(t, d)
        assert v == pytest.approx(1.0 - sf.relative_risk(t, d), abs=1e-14)
        assert v <= 1.0


def test_rejects_no_false_negative() -> None:
    with pytest.raises(ValueError):
        sf.relative_risk_reduction([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
