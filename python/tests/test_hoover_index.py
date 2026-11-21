"""The Hoover index (ADR 0512)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_largest_gap_below_the_lorenz_curve() -> None:
    rng = np.random.default_rng(275)
    for n in range(1, 30):
        x = rng.random(n) * 10
        lorenz = np.concatenate([[0.0], np.cumsum(np.sort(x)) / np.sum(x)])
        want = float(np.max(np.arange(n + 1) / n - lorenz))
        v = sf.hoover_index(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert sf.hoover_index(3.5 * x) == pytest.approx(v, rel=1e-12, abs=1e-14)
        assert 0 <= v <= 1 - 1 / n + 1e-14


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hoover_index(bad)
