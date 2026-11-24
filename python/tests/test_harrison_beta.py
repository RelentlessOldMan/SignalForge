"""Harrison's beta of two presence records (ADR 0589)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(589)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        gamma = int(np.count_nonzero((x > 0) | (y > 0)))
        alpha_max = max(int(np.count_nonzero(x > 0)), int(np.count_nonzero(y > 0)))
        got = sf.harrison_beta(x, y)
        assert got == pytest.approx(gamma / alpha_max - 1.0, abs=1e-15)
        assert sf.harrison_beta(y, x) == got
        assert 0.0 <= got <= 1.0


def test_special_cases() -> None:
    assert sf.harrison_beta([1.0, 2.0, 3.0, 0.0], [1e300, 0.0, 0.0, 0.0]) == 0.0
    assert sf.harrison_beta([1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]) == 1.0


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 2.0]),
        ([1.0, -1.0], [1.0, 2.0]),
        ([1.0, np.nan], [1.0, 2.0]),
        ([[1.0, 2.0]], [[1.0, 2.0]]),
    ],
)
def test_rejects_bad_arguments(x: list[float], y: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.harrison_beta(x, y)
