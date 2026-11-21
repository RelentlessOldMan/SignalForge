"""The Herfindahl index (ADR 0523)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_coefficient_of_variation() -> None:
    rng = np.random.default_rng(286)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        h = sf.herfindahl_index(x)
        cv = sf.coefficient_of_variation(x)
        assert h == pytest.approx((1 + cv * cv) / n, rel=1e-12, abs=1e-14)
        assert 1 / n - 1e-14 <= h <= 1
        assert sf.herfindahl_index(3.5 * x) == pytest.approx(h, rel=1e-12, abs=1e-14)
    assert sf.herfindahl_index([2.0] * 8) == pytest.approx(0.125, rel=1e-15)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.herfindahl_index(bad)
