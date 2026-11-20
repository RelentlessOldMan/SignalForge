"""The Maxwell-Pilliner coefficient (ADR 0458)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_no_larger_than_phi() -> None:
    rng = np.random.default_rng(221)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.maxwell_pilliner_coefficient(t, d)
        assert -1.0 <= v <= 1.0
        assert v == sf.maxwell_pilliner_coefficient(d, t)
        assert abs(v) <= abs(float(np.corrcoef(t, d)[0, 1])) + 1e-15


def test_changes_sign_when_one_record_is_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    v = sf.maxwell_pilliner_coefficient(t, d)
    assert sf.maxwell_pilliner_coefficient(t, 1 - d) == -v
    assert sf.maxwell_pilliner_coefficient(1 - t, 1 - d) == v


def test_rejects_two_constant_records() -> None:
    with pytest.raises(ValueError):
        sf.maxwell_pilliner_coefficient([1.0, 1.0], [0.0, 0.0])
