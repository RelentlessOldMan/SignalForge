"""Slicer (ADR 0294)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_open_fraction_matches_duty() -> None:
    x = np.ones(48000)
    y = sf.slicer(x, 8.0, 0.25, 48000.0)
    assert np.count_nonzero(y) == 12000
    assert np.all(y[:1500] == 1.0)
    assert np.all(y[1500:6000] == 0.0)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.slicer([1j], 1.0, 0.5, 8.0)
