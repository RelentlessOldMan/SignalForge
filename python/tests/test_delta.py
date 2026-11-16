"""Delta coefficients (conventions: Delta coefficients; ADR 0158)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("width", [1, 2, 3])
def test_ramp_interior_is_the_slope(width: int) -> None:
    t = np.arange(20.0)
    d = sf.delta(np.column_stack([0.5 * t - 3, -2 * t]), width)
    assert d[width:-width] == pytest.approx(np.tile([0.5, -2.0], (20 - 2 * width, 1)))


def test_constant_gives_zeros_and_delta_is_linear() -> None:
    assert np.all(sf.delta(np.full((5, 3), 4.0)) == 0)
    rng = np.random.default_rng(2)
    a, b = rng.standard_normal((9, 4)), rng.standard_normal((9, 4))
    assert sf.delta(2 * a + b) == pytest.approx(2 * sf.delta(a) + sf.delta(b), abs=1e-12)


def test_rejects_ragged_frames() -> None:
    with pytest.raises(ValueError):
        sf.delta([[1.0, 2.0], [3.0]])
