"""The Hannah-Kay index (ADR 0527)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_power_sums_and_herfindahl() -> None:
    rng = np.random.default_rng(290)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        prev = float(n) + 1e-12
        for alpha in [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 7.0]:
            h = sf.hannah_kay_index(x, alpha)
            if alpha == 1.0:
                want = float(np.exp(-np.sum(sh * np.log(sh))))
            else:
                want = float(np.sum(sh**alpha) ** (1 / (1 - alpha)))
            assert h == pytest.approx(want, rel=1e-12)
            assert 1 - 1e-12 <= h <= prev
            prev = h + 1e-12
        assert sf.hannah_kay_index(x, 2.0) == pytest.approx(1 / sf.herfindahl_index(x), rel=1e-12)
        near = sf.hannah_kay_index(x, 1.0 + 1e-7)
        assert near == pytest.approx(sf.hannah_kay_index(x, 1.0), rel=1e-5)


@pytest.mark.parametrize(
    ("bad", "alpha"),
    [
        ([], 2.0),
        ([1.0, -1.0], 2.0),
        ([0.0, 0.0], 2.0),
        ([1.0, np.inf], 2.0),
        ([[1.0, 2.0]], 2.0),
        ([1.0, 2.0], 0.0),
        ([1.0, 2.0], -1.0),
        ([1.0, 2.0], np.nan),
        ([1.0, 2.0], np.inf),
    ],
)
def test_rejects_bad_arguments(bad: list[float], alpha: float) -> None:
    with pytest.raises(ValueError):
        sf.hannah_kay_index(bad, alpha)
