"""The McIntosh dominance (ADR 0539)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_euclidean_length() -> None:
    rng = np.random.default_rng(302)
    for n in range(1, 30):
        x = rng.integers(0, 20, n).astype(float)
        x[0] += 2.0
        total = float(np.sum(x))
        d = sf.mcintosh_dominance(x)
        want = (total - float(np.linalg.norm(x))) / (total - math.sqrt(total))
        assert d == pytest.approx(want, rel=1e-12, abs=1e-14)
        assert -1e-14 <= d <= 1 + 1e-14
    assert sf.mcintosh_dominance([0.0, 7.0, 0.0]) == pytest.approx(0.0, abs=1e-15)
    assert sf.mcintosh_dominance([1.0] * 16) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize(
    "bad", [[], [1.0, -1.0], [0.0, 0.0], [0.5, 0.5], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.mcintosh_dominance(bad)
