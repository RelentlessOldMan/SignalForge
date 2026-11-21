"""Heip's evenness (ADR 0531)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_entropy_and_hannah_kay() -> None:
    rng = np.random.default_rng(294)
    for n in range(2, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        e = sf.heip_evenness(x)
        want = (math.exp(float(-np.sum(sh * np.log(sh)))) - 1) / (n - 1)
        assert e == pytest.approx(want, rel=1e-12)
        assert e == pytest.approx((sf.hannah_kay_index(x, 1.0) - 1) / (n - 1), rel=1e-12)
        assert 0 <= e <= 1 + 1e-14
        assert sf.heip_evenness(3.5 * x) == pytest.approx(e, rel=1e-12)
    assert sf.heip_evenness([2.0] * 8) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.heip_evenness(bad)
