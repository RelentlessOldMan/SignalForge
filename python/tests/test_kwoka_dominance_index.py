"""The Kwoka dominance index (ADR 0526)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_ranked_gaps_and_bounds() -> None:
    rng = np.random.default_rng(289)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        shares = np.sort(x)[::-1] / np.sum(x)
        want = float(np.sum(np.diff(shares) ** 2))
        d = sf.kwoka_dominance_index(x)
        assert d == pytest.approx(want, rel=1e-12, abs=1e-15)
        assert 0 <= d <= float(shares[0]) ** 2 + 1e-15
        assert d <= sf.herfindahl_index(x) + 1e-15
        assert sf.kwoka_dominance_index(3.5 * x) == pytest.approx(d, rel=1e-12, abs=1e-15)
    assert sf.kwoka_dominance_index([2.0] * 8) == 0.0


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.kwoka_dominance_index(bad)
