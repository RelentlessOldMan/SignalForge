"""Bulla's evenness (ADR 0535)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_overlap() -> None:
    rng = np.random.default_rng(298)
    for n in range(2, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        o = float(np.sum(np.minimum(sh, 1 / n)))
        e = sf.bulla_evenness(x)
        assert e == pytest.approx((o - 1 / n) / (1 - 1 / n), rel=1e-12, abs=1e-14)
        assert 0 <= e <= 1 + 1e-14
        assert sf.bulla_evenness(3.5 * x) == pytest.approx(e, rel=1e-12, abs=1e-14)
    assert sf.bulla_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-15)
    assert sf.bulla_evenness([0.0] * 7 + [3.0]) == 0.0


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.bulla_evenness(bad)
