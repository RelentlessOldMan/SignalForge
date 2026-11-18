"""Mid/side coding (ADR 0264)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_round_trip() -> None:
    rng = np.random.default_rng(33)
    left, right = rng.standard_normal(500), rng.standard_normal(500)
    ms = sf.mid_side_encode(left, right)
    lr = sf.mid_side_decode(ms.mid, ms.side)
    assert np.allclose(lr.left, left, rtol=0, atol=1e-15)
    assert np.allclose(lr.right, right, rtol=0, atol=1e-15)


def test_mono_has_no_side() -> None:
    x = np.sin(np.arange(100) / 7)
    ms = sf.mid_side_encode(x, x)
    assert np.array_equal(ms.mid, x)
    assert np.all(ms.side == 0)


def test_rejects_complex() -> None:
    with pytest.raises(ValueError):
        sf.mid_side_encode(np.array([1j]), np.array([1.0]))
