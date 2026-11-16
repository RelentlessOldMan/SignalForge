"""Fractional-octave bands (conventions: Fractional-octave bands; ADR 0167)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_bands_tile_without_gaps_and_contain_1khz_exactly() -> None:
    rows = sf.octave_bands(3, 20.0, 20000.0)
    assert rows.shape == (30, 3)
    assert rows[1:, 0] == pytest.approx(rows[:-1, 2], rel=1e-13)
    assert 1000.0 in rows[:, 1]
    assert np.all(rows[:, 2] / rows[:, 0] == pytest.approx(10 ** (0.3 / 3), rel=1e-13))


def test_an_empty_range_gives_no_rows() -> None:
    assert sf.octave_bands(1, 1100.0, 1900.0).shape == (0, 3)
