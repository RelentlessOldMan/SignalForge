"""The Lorenz curve (ADR 0517)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_gives_the_gini_and_hoover_measures() -> None:
    rng = np.random.default_rng(280)
    for n in range(1, 30):
        x = rng.random(n) * 10
        lc = sf.lorenz_curve(x)
        assert lc.shape == (n + 1,)
        assert lc[0] == 0.0
        assert lc[-1] == 1.0
        assert np.all(np.diff(lc) >= 0)
        k = np.arange(n + 1) / n
        assert np.all(lc <= k + 1e-15)
        area = float(np.sum((lc[1:] + lc[:-1]) / 2)) / n
        assert 1 - 2 * area == pytest.approx(sf.gini_coefficient(x), rel=1e-12, abs=1e-14)
        assert float(np.max(k - lc)) == pytest.approx(sf.hoover_index(x), rel=1e-12, abs=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.lorenz_curve(bad)
