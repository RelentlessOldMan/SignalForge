"""The mean log deviation (ADR 0514)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_of_the_arithmetic_over_the_geometric_mean() -> None:
    rng = np.random.default_rng(277)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        want = math.log(float(np.mean(x))) - float(np.mean(np.log(x)))
        v = sf.mean_log_deviation(x)
        assert v == pytest.approx(want, rel=1e-11, abs=1e-14)
        assert sf.mean_log_deviation(3.5 * x) == pytest.approx(v, rel=1e-11, abs=1e-14)
        assert v >= -1e-15


@pytest.mark.parametrize("bad", [[], [1.0, 0.0], [-2.0, 1.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.mean_log_deviation(bad)
