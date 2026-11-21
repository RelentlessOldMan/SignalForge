"""The Atkinson index (ADR 0515)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_geometric_and_harmonic_means() -> None:
    rng = np.random.default_rng(278)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        mean = float(np.mean(x))
        geo = 1 - math.exp(-sf.mean_log_deviation(x))
        assert sf.atkinson_index(x, 1.0) == pytest.approx(geo, rel=1e-11, abs=1e-14)
        harm = 1 - n / float(np.sum(1 / x)) / mean
        assert sf.atkinson_index(x, 2.0) == pytest.approx(harm, rel=1e-11, abs=1e-14)
        assert sf.atkinson_index(x, 0.0) == pytest.approx(0.0, abs=1e-14)
        vals = [sf.atkinson_index(x, e) for e in (0.25, 0.5, 1.0, 1.5, 3.0)]
        assert all(a <= b + 1e-14 for a, b in itertools.pairwise(vals))
        assert sf.atkinson_index(3.5 * x, 1.5) == pytest.approx(vals[3], rel=1e-11, abs=1e-14)


@pytest.mark.parametrize("bad", [[], [1.0, 0.0], [-2.0, 1.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.atkinson_index(bad, 1.0)


def test_rejects_a_negative_epsilon() -> None:
    with pytest.raises(ValueError):
        sf.atkinson_index([1.0, 2.0], -0.1)
