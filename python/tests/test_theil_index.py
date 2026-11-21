"""The Theil index (ADR 0511)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_ln_n_less_the_entropy_of_the_shares() -> None:
    rng = np.random.default_rng(274)
    for n in range(1, 30):
        x = rng.random(n) * 10
        p = x / np.sum(x)
        want = math.log(n) + float(np.sum(p * np.log(p)))
        v = sf.theil_index(x)
        assert v == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert sf.theil_index(3.5 * x) == pytest.approx(v, rel=1e-12, abs=1e-14)
        assert -1e-15 <= v <= math.log(n) + 1e-14


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.theil_index(bad)
