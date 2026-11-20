"""Fossum's coefficient (ADR 0449)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_not_negative() -> None:
    rng = np.random.default_rng(212)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0] = d[0] = 1.0
        v = sf.fossum_coefficient(t, d)
        assert v >= 0.0
        assert v == sf.fossum_coefficient(d, t)


def test_identical_records_give_n_times_the_corrected_share_squared() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert sf.fossum_coefficient(t, t) == pytest.approx(8 * (2.5 / 3) ** 2, rel=1e-15)


def test_rejects_a_record_with_no_one() -> None:
    with pytest.raises(ValueError):
        sf.fossum_coefficient([0.0, 1.0], [0.0, 0.0])
