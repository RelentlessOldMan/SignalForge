"""The mutual information of two binary records (ADR 0464)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_at_most_either_entropy() -> None:
    rng = np.random.default_rng(227)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        v = sf.binary_mutual_information(t, d)
        assert v == pytest.approx(sf.binary_mutual_information(d, t), rel=1e-13, abs=1e-15)
        assert v == pytest.approx(sf.binary_mutual_information(1 - t, d), rel=1e-13, abs=1e-15)
        for r in (t, d):
            p = float(r.mean())
            h = -sum(q * math.log(q) for q in (p, 1 - p) if q > 0)
            assert -1e-15 <= v <= h + 1e-14


def test_of_a_record_with_itself_is_its_entropy() -> None:
    t = np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    h = -(0.25 * math.log(0.25) + 0.75 * math.log(0.75))
    assert sf.binary_mutual_information(t, t) == pytest.approx(h, rel=1e-14)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.binary_mutual_information([1.0, 0.0], [1.0])
