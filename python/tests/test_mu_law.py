"""mu-law companding (ADR 0248)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_round_trip() -> None:
    x = np.random.default_rng(23).uniform(-1, 1, 1000)
    assert np.allclose(sf.mu_law_expand(sf.mu_law_compress(x)), x, rtol=0, atol=1e-15)


def test_compress_is_odd_and_monotonic() -> None:
    x = np.arange(-100, 101) / 100
    y = sf.mu_law_compress(x, 50.0)
    assert np.all(np.diff(y) > 0)
    assert np.allclose(y, -y[::-1], rtol=0, atol=0)


def test_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        sf.mu_law_compress([1.0001])
