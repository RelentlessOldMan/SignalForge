"""The Palma ratio (ADR 0518)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_reads_the_palma_ratio_joined_by_lines() -> None:
    rng = np.random.default_rng(281)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        lc = sf.lorenz_curve(x)
        k = np.arange(n + 1) / n
        want = (1 - float(np.interp(0.9, k, lc))) / float(np.interp(0.4, k, lc))
        v = sf.palma_ratio(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert sf.palma_ratio(3.5 * x) == pytest.approx(v, rel=1e-12, abs=1e-14)
    assert sf.palma_ratio([2.0] * 7) == pytest.approx(0.25, rel=1e-14)


@pytest.mark.parametrize(
    "bad", [[], [1.0, -1.0], [0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 9.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.palma_ratio(bad)
