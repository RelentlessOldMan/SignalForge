"""The Zenga index (ADR 0521)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_mean_ratios_and_bounds_bonferroni() -> None:
    rng = np.random.default_rng(284)
    for n in range(2, 30):
        x = rng.random(n) * 10
        v = np.sort(x)
        ratios = [float(np.mean(v[:k])) / float(np.mean(v[k:])) for k in range(1, n)]
        z = sf.zenga_index(x)
        assert z == pytest.approx(1 - float(np.mean(ratios)), rel=1e-12, abs=1e-14)
        assert sf.bonferroni_index(x) - 1e-14 <= z <= 1
        assert sf.zenga_index(3.5 * x) == pytest.approx(z, rel=1e-12, abs=1e-14)
    assert sf.zenga_index([2.0] * 7) == pytest.approx(0.0, abs=1e-15)


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.zenga_index(bad)
