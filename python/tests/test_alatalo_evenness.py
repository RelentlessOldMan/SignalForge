"""Alatalo's evenness (ADR 0537)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_hill_numbers() -> None:
    rng = np.random.default_rng(300)
    for n in range(2, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        n2 = 1 / float(np.sum(sh * sh))
        n1 = math.exp(float(-np.sum(sh * np.log(sh))))
        f = sf.alatalo_evenness(x)
        assert f == pytest.approx((n2 - 1) / (n1 - 1), rel=1e-11)
        hk2, hk1 = sf.hannah_kay_index(x, 2.0), sf.hannah_kay_index(x, 1.0)
        assert f == pytest.approx((hk2 - 1) / (hk1 - 1), rel=1e-11)
        assert 0 < f <= 1 + 1e-12
        assert sf.alatalo_evenness(np.append(x, 0.0)) == pytest.approx(f, rel=1e-11)
    assert sf.alatalo_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-13)


@pytest.mark.parametrize(
    "bad", [[], [5.0], [0.0, 3.0, 0.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.alatalo_evenness(bad)
