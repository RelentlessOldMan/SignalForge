"""Michael's coefficient (ADR 0442)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_cell_formula() -> None:
    rng = np.random.default_rng(205)
    for _ in range(20):
        t = rng.random(30) < 0.4
        d = rng.random(30) < 0.5
        tp, tn = np.sum(t & d), np.sum(~t & ~d)
        fn, fp = np.sum(t & ~d), np.sum(~t & d)
        want = 4 * (tp * tn - fn * fp) / ((tp + tn) ** 2 + (fn + fp) ** 2)
        got = sf.michael_coefficient(t.astype(float), d.astype(float))
        assert got == pytest.approx(want, rel=1e-14, abs=1e-15)


def test_is_defined_for_constant_records() -> None:
    assert sf.michael_coefficient([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_rejects_a_value_other_than_zero_or_one() -> None:
    with pytest.raises(ValueError):
        sf.michael_coefficient([1.0, 0.5], [0.0, 1.0])
