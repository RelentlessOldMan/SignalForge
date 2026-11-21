"""The Berger-Parker index (ADR 0530)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_largest_share_and_the_concentration_ratio() -> None:
    rng = np.random.default_rng(293)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        d = sf.berger_parker_index(x)
        assert d == pytest.approx(float(np.max(x) / np.sum(x)), rel=1e-15)
        assert d == pytest.approx(sf.concentration_ratio(x, 1), rel=1e-15)
        assert 1 / n - 1e-15 <= d <= 1
        assert sf.berger_parker_index(3.5 * x) == pytest.approx(d, rel=1e-14)
    assert sf.berger_parker_index([2.0] * 8) == 0.125


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.berger_parker_index(bad)
