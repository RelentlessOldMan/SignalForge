"""The Hall-Tideman index (ADR 0525)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_ranked_shares_and_the_gini_coefficient() -> None:
    rng = np.random.default_rng(288)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        shares = np.sort(x)[::-1] / np.sum(x)
        want = 1 / (2 * float(np.sum(np.arange(1, n + 1) * shares)) - 1)
        h = sf.hall_tideman_index(x)
        assert h == pytest.approx(want, rel=1e-12)
        assert h == pytest.approx(1 / (n * (1 - sf.gini_coefficient(x))), rel=1e-12)
        assert 1 / n - 1e-14 <= h <= 1
        assert sf.hall_tideman_index(3.5 * x) == pytest.approx(h, rel=1e-12)
    assert sf.hall_tideman_index([2.0] * 8) == pytest.approx(0.125, rel=1e-15)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hall_tideman_index(bad)
