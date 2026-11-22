"""The Hill ratio evenness (ADR 0536)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_hill_numbers() -> None:
    rng = np.random.default_rng(299)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        n2 = 1 / float(np.sum(sh * sh))
        n1 = math.exp(float(-np.sum(sh * np.log(sh))))
        e = sf.hill_ratio_evenness(x)
        assert e == pytest.approx(n2 / n1, rel=1e-12)
        hk = sf.hannah_kay_index(x, 2.0) / sf.hannah_kay_index(x, 1.0)
        assert e == pytest.approx(hk, rel=1e-12)
        assert 0 < e <= 1 + 1e-14
        assert sf.hill_ratio_evenness(np.append(x, 0.0)) == pytest.approx(e, rel=1e-12)
    assert sf.hill_ratio_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hill_ratio_evenness(bad)
