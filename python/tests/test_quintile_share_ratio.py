"""The quintile share ratio (ADR 0519)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_reads_the_lorenz_curve_joined_by_lines() -> None:
    rng = np.random.default_rng(282)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        lc = sf.lorenz_curve(x)
        k = np.arange(n + 1) / n
        want = (1 - float(np.interp(0.8, k, lc))) / float(np.interp(0.2, k, lc))
        v = sf.quintile_share_ratio(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert v >= 1 - 1e-14
        assert sf.quintile_share_ratio(3.5 * x) == pytest.approx(v, rel=1e-12, abs=1e-14)
    assert sf.quintile_share_ratio([2.0] * 7) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize(
    "bad", [[], [1.0, -1.0], [0.0, 0.0], [0.0, 0.0, 9.0, 9.0, 9.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.quintile_share_ratio(bad)
