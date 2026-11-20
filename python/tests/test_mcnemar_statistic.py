"""McNemar's statistic (ADR 0479)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(242)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0], d[0] = 1.0, 0.0
        v = sf.mcnemar_statistic(t, d)
        assert v == sf.mcnemar_statistic(d, t)
        assert 0.0 <= v <= float(np.sum(t != d))


def test_rejects_records_that_agree_everywhere() -> None:
    with pytest.raises(ValueError):
        sf.mcnemar_statistic([1.0, 0.0], [1.0, 0.0])
