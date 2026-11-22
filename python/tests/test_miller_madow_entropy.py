"""The Miller-Madow entropy (ADR 0555)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_plug_in_plus_the_bias_term() -> None:
    rng = np.random.default_rng(318)
    for n in range(1, 40):
        x = rng.integers(0, 10, n).astype(float)
        x[0] += 1.0
        total = float(np.sum(x))
        p = x[x > 0] / total
        expected = float(-np.sum(p * np.log(p))) + (p.size - 1) / (2 * total)
        h = sf.miller_madow_entropy(x)
        assert h == pytest.approx(expected, rel=1e-13, abs=1e-15)
        assert h >= 0
        assert sf.miller_madow_entropy(rng.permutation(x)) == pytest.approx(h, rel=1e-13, abs=1e-15)
    assert sf.miller_madow_entropy([0.0, 7.0]) == 0.0


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [np.nan]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.miller_madow_entropy(bad)
