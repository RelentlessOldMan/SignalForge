"""The attributable fraction (ADR 0485)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_less_the_reciprocal_attributable_fraction() -> None:
    rng = np.random.default_rng(248)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        v = sf.attributable_fraction(t, d)
        assert v == pytest.approx(1 - 1 / sf.relative_risk(t, d), abs=1e-14)
        assert v <= 1.0


def test_rejects_records_that_share_no_one() -> None:
    with pytest.raises(ValueError):
        sf.attributable_fraction([1.0, 0.0], [0.0, 1.0])
