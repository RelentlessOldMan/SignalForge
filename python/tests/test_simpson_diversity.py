"""The Gini-Simpson index (ADR 0529)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_squared_shares_and_herfindahl() -> None:
    rng = np.random.default_rng(292)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        d = sf.simpson_diversity(x)
        assert d == pytest.approx(1 - float(np.sum(sh * sh)), rel=1e-12, abs=1e-15)
        assert d == pytest.approx(1 - sf.herfindahl_index(x), rel=1e-12, abs=1e-15)
        assert 0 <= d <= 1 - 1 / n + 1e-14
        assert sf.simpson_diversity(3.5 * x) == pytest.approx(d, rel=1e-12, abs=1e-15)
    assert sf.simpson_diversity([2.0] * 8) == pytest.approx(0.875, rel=1e-15)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.simpson_diversity(bad)
