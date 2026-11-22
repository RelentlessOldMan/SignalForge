"""The Brillouin index (ADR 0546)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_log_gamma() -> None:
    rng = np.random.default_rng(309)
    for n in range(1, 30):
        x = rng.integers(0, 30, n).astype(float)
        x[0] += 1.0
        total = float(np.sum(x))
        hb = sf.brillouin_index(x)
        want = (math.lgamma(total + 1) - sum(math.lgamma(a + 1) for a in x)) / total
        assert hb == pytest.approx(want, rel=1e-11, abs=1e-13)
        sh = x[x > 0] / total
        assert 0 <= hb <= float(-np.sum(sh * np.log(sh))) + 1e-12
    assert sf.brillouin_index([0.0, 9.0]) == 0.0


@pytest.mark.parametrize(
    "bad", [[], [1.0, -1.0], [0.0, 0.0], [1.5], [1e7, 1.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.brillouin_index(bad)
