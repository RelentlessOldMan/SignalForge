"""The ACE richness (ADR 0551)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_frequency_counts() -> None:
    rng = np.random.default_rng(314)
    for n in range(1, 40):
        x = rng.integers(0, 15, n).astype(float)
        x[0] = 2.0
        f = np.bincount(x.astype(int), minlength=11)[:11]
        s_rare = int(np.sum(f[1:]))
        n_rare = float(np.sum(np.arange(11) * f))
        c = 1 - f[1] / n_rare
        p = float(np.sum(np.arange(11) * (np.arange(11) - 1) * f))
        g = max(s_rare / c * p / (n_rare * (n_rare - 1)) - 1, 0.0)
        expected = np.count_nonzero(x > 10) + s_rare / c + f[1] / c * g
        s = sf.ace_richness(x)
        assert s == pytest.approx(expected, rel=1e-13)
        assert s >= np.count_nonzero(x) - 1e-12
        assert sf.ace_richness(rng.permutation(x)) == pytest.approx(s, rel=1e-13)
    assert sf.ace_richness([12.0, 40.0, 0.0]) == 2.0


@pytest.mark.parametrize(
    "bad", [[], [1.0], [1.0, 1.0], [20.0, 1.0], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.ace_richness(bad)
