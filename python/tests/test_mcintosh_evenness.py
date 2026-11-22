"""The McIntosh evenness (ADR 0540)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_euclidean_length() -> None:
    rng = np.random.default_rng(303)
    for n in range(2, 30):
        x = rng.random(n) * 10 + 0.1
        total = float(np.sum(x))
        e = sf.mcintosh_evenness(x)
        want = (total - float(np.linalg.norm(x))) / (total - total / math.sqrt(n))
        assert e == pytest.approx(want, rel=1e-12)
        assert -1e-14 <= e <= 1 + 1e-14
        assert sf.mcintosh_evenness(0.01 * x) == pytest.approx(e, rel=1e-11)
    assert sf.mcintosh_evenness([0.0, 7.0, 0.0]) == pytest.approx(0.0, abs=1e-15)
    assert sf.mcintosh_evenness([0.3] * 16) == pytest.approx(1.0, rel=1e-13)


@pytest.mark.parametrize("bad", [[], [5.0], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.mcintosh_evenness(bad)
