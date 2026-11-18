"""Peak normalization (ADR 0268)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_peak_reached() -> None:
    rng = np.random.default_rng(36)
    x = rng.standard_normal(300) + 1j * rng.standard_normal(300)
    y = sf.normalize_peak(x, 0.7)
    assert abs(np.max(np.abs(y)) - 0.7) < 1e-15
    assert np.allclose(y / x, (y / x)[0], rtol=1e-15, atol=0)


def test_real_stays_real() -> None:
    y = sf.normalize_peak([1.0, -3.0])
    assert not np.iscomplexobj(y)
    assert np.array_equal(y, [1 / 3, -1.0])


def test_rejects_silence() -> None:
    with pytest.raises(ValueError):
        sf.normalize_peak([0.0])
