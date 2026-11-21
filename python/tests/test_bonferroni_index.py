"""The Bonferroni index (ADR 0520)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_mean_gaps_and_the_lorenz_curve() -> None:
    rng = np.random.default_rng(283)
    for n in range(2, 30):
        x = rng.random(n) * 10
        v = np.sort(x)
        mu = float(np.mean(v))
        gaps = [(mu - float(np.mean(v[:k]))) / mu for k in range(1, n)]
        b = sf.bonferroni_index(x)
        assert b == pytest.approx(float(np.mean(gaps)), rel=1e-12, abs=1e-14)
        lc = sf.lorenz_curve(x)
        k = np.arange(1, n)
        assert b == pytest.approx(1 - float(np.mean(lc[1:n] * n / k)), rel=1e-12, abs=1e-14)
        assert 0 <= b <= 1
        assert sf.bonferroni_index(3.5 * x) == pytest.approx(b, rel=1e-12, abs=1e-14)
    assert sf.bonferroni_index([2.0] * 7) == pytest.approx(0.0, abs=1e-15)


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.bonferroni_index(bad)
