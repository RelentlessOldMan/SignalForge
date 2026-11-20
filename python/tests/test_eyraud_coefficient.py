"""Eyraud's coefficient (ADR 0450)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_changes_sign_when_a_record_is_flipped() -> None:
    rng = np.random.default_rng(213)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = d[:2] = [1.0, 0.0]
        v = sf.eyraud_coefficient(t, d)
        assert v == sf.eyraud_coefficient(d, t)
        assert sf.eyraud_coefficient(t, 1 - d) == pytest.approx(-v, rel=1e-14, abs=1e-15)


def test_identical_records_give_n_squared_over_the_margins() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert sf.eyraud_coefficient(t, t) == pytest.approx(64 / 15, rel=1e-15)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.eyraud_coefficient([0.0, 1.0], [1.0, 1.0])
