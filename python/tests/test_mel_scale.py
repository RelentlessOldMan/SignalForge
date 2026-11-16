"""Mel scale (conventions: Mel scale; ADR 0154)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

GRID = np.linspace(0.0, 20000.0, 401)


@pytest.mark.parametrize("scale", ["htk", "slaney"])
def test_inverse_on_a_grid(scale: str) -> None:
    back = sf.mel_to_hz(sf.hz_to_mel(GRID, scale=scale), scale=scale)
    assert back == pytest.approx(GRID, rel=1e-12, abs=1e-9)


@pytest.mark.parametrize("scale", ["htk", "slaney"])
def test_increasing(scale: str) -> None:
    assert np.all(np.diff(sf.hz_to_mel(GRID, scale=scale)) > 0)


def test_arrays_map_elementwise_and_scalars_give_floats() -> None:
    m = sf.hz_to_mel([0.0, 6300.0])
    assert isinstance(m, np.ndarray) and m == pytest.approx([0.0, 2595.0])
    assert isinstance(sf.mel_to_hz(15.0, scale="slaney"), float)


def test_one_bad_element_rejects_the_array() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        sf.hz_to_mel([100.0, -1.0])
