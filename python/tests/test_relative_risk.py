"""The relative risk (ADR 0484)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_ratio_of_the_two_risks() -> None:
    rng = np.random.default_rng(247)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        exposed = float(np.sum(t * d)) / float(np.sum(d))
        unexposed = float(np.sum(t * (1 - d))) / float(np.sum(1 - d))
        v = sf.relative_risk(t, d)
        assert v == pytest.approx(exposed / unexposed, rel=1e-14)
        assert v >= 0.0


def test_rejects_a_decision_with_no_false_negative() -> None:
    with pytest.raises(ValueError):
        sf.relative_risk([1.0, 0.0], [1.0, 0.0])
