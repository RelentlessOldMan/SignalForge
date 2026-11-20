"""The population attributable fraction (ADR 0486)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_exposed_fraction_scaled_by_the_exposed_share_of_cases() -> None:
    rng = np.random.default_rng(249)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        share = float(np.sum(t * d)) / float(np.sum(t))
        v = sf.population_attributable_fraction(t, d)
        assert v == pytest.approx(sf.attributable_fraction(t, d) * share, abs=1e-14)
        assert v <= 1.0


def test_rejects_a_decision_with_no_zero() -> None:
    with pytest.raises(ValueError):
        sf.population_attributable_fraction([1.0, 0.0], [1.0, 1.0])
