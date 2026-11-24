"""Vanderploeg and Scavia's relativized electivity (ADR 0605)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(605)
    for _ in range(20):
        x = rng.uniform(0.0, 4.0, 12) * (rng.uniform(size=12) < 0.6)
        available = rng.uniform(0.5, 4.0, 12)
        x[0] = 1.0
        w = x / available
        alpha = w / w.sum()
        got = sf.vanderploeg_scavia_electivity(x, available)
        np.testing.assert_allclose(got, (alpha - 1 / 12) / (alpha + 1 / 12), rtol=1e-13, atol=1e-15)
        assert np.all(np.abs(got) <= 1.0)
        assert np.all(got[x == 0] == -1.0)
        np.testing.assert_allclose(
            sf.vanderploeg_scavia_electivity(3.0 * x, 0.5 * available),
            got,
            rtol=1e-13,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            sf.vanderploeg_scavia_electivity(available, available), np.zeros(12), atol=1e-14
        )


def test_special_cases() -> None:
    np.testing.assert_allclose(
        sf.vanderploeg_scavia_electivity([1.0, 1.0], [1.0, 3.0]), [0.2, -1 / 3]
    )
    np.testing.assert_allclose(
        sf.vanderploeg_scavia_electivity([1.0, 0.0], [1.0, 3.0]), [1 / 3, -1.0]
    )
    np.testing.assert_array_equal(sf.vanderploeg_scavia_electivity([2.0], [5.0]), [0.0])


@pytest.mark.parametrize(
    ("x", "available"),
    [
        ([], []),
        ([1.0, 2.0], [1.0]),
        ([0.0, 0.0], [1.0, 1.0]),
        ([1.0, -1.0], [1.0, 1.0]),
        ([1.0, np.nan], [1.0, 1.0]),
        ([[1.0, 2.0]], [[1.0, 1.0]]),
        ([1.0, 2.0], [1.0, 0.0]),
        ([1.0, 2.0, 3.0], [1e300, 5e-324, 1.0]),
        ([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]),
    ],
)
def test_rejects_bad_arguments(x: list[float], available: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.vanderploeg_scavia_electivity(x, available)
