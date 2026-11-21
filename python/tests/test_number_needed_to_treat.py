"""The number needed to treat (ADR 0504)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_reciprocal_of_the_number_needed_to_treat() -> None:
    rng = np.random.default_rng(267)
    checked = 0
    for _ in range(40):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        rd = sf.risk_difference(t, d)
        if rd == 0:
            continue
        v = sf.number_needed_to_treat(t, d)
        assert v == pytest.approx(1.0 / rd, rel=1e-14)
        assert sf.number_needed_to_treat(1 - t, d) == pytest.approx(-v, rel=1e-15)
        checked += 1
    assert checked > 20


def test_rejects_a_number_needed_to_treat_of_zero() -> None:
    with pytest.raises(ValueError):
        sf.number_needed_to_treat([1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0])
