"""Wilson and Shmida's beta of two presence records (ADR 0591)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_bray_curtis_on_presence() -> None:
    rng = np.random.default_rng(591)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        y = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        x[0] = 1.0
        y[1] = 1.0
        px = (x > 0).astype(np.float64)
        py = (y > 0).astype(np.float64)
        got = sf.wilson_shmida_beta(x, y)
        assert got == pytest.approx(sf.bray_curtis(px, py), abs=1e-15)
        assert sf.wilson_shmida_beta(y, x) == got
        assert got == pytest.approx(sf.cody_beta(x, y) / ((px.sum() + py.sum()) / 2), abs=1e-15)


def test_special_cases() -> None:
    assert sf.wilson_shmida_beta([1.0, 2.0, 3.0, 0.0], [1e300, 4.0, 0.5, 0.0]) == 0.0
    assert sf.wilson_shmida_beta([1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]) == 1.0


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
        sf.wilson_shmida_beta(x, y)
