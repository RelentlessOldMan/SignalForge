"""Stereo width (ADR 0267)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_mid_side_with_scaled_side() -> None:
    rng = np.random.default_rng(35)
    left, right = rng.standard_normal(200), rng.standard_normal(200)
    ms = sf.mid_side_encode(left, right)
    want = sf.mid_side_decode(ms.mid, ms.side * 1.75)
    got = sf.stereo_width(left, right, 1.75)
    assert np.array_equal(got.left, want.left)
    assert np.array_equal(got.right, want.right)


def test_zero_width_is_mono() -> None:
    lr = sf.stereo_width([1.0, 2.0], [3.0, -2.0], 0.0)
    assert np.array_equal(lr.left, lr.right)


def test_rejects_negative_width() -> None:
    with pytest.raises(ValueError):
        sf.stereo_width([1.0], [1.0], -1.0)
