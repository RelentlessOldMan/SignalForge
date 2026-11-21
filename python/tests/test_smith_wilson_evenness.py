"""The Smith-Wilson evenness (ADR 0534)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_variance_of_the_logs() -> None:
    rng = np.random.default_rng(297)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        want = 1 - 2 / math.pi * math.atan(float(np.var(np.log(x))))
        e = sf.smith_wilson_evenness(x)
        assert e == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert 0 < e <= 1
        assert sf.smith_wilson_evenness(3.5 * x) == pytest.approx(e, rel=1e-12, abs=1e-14)
    assert sf.smith_wilson_evenness([2.0] * 8) == 1.0
    assert sf.smith_wilson_evenness([1.0, math.e**2]) == pytest.approx(0.5, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, 0.0], [1.0, -1.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.smith_wilson_evenness(bad)
