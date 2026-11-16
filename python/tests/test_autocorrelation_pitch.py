"""Autocorrelation pitch (conventions: Autocorrelation pitch; ADR 0150)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

FS = 8000.0
F0 = 8000.0 / 36.6  # a period of 36.6 samples, not a whole lag
X = np.sin(2 * np.pi * F0 * np.arange(1200) / FS) + 0.4 * np.sin(
    4 * np.pi * F0 * np.arange(1200) / FS
)


def test_recovers_a_non_integer_period() -> None:
    p = sf.autocorrelation_pitch(X, FS, 80.0, 500.0)
    assert p.frequency == pytest.approx(F0, rel=5e-3)
    assert p.voicing > 0.9


def test_scaling_leaves_it_unchanged() -> None:
    a = sf.autocorrelation_pitch(X, FS, 80.0, 500.0)
    b = sf.autocorrelation_pitch(-3.0 * X, FS, 80.0, 500.0)
    assert (b.frequency, b.lag, b.voicing) == pytest.approx((a.frequency, a.lag, a.voicing))


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError, match="real"):
        sf.autocorrelation_pitch(X + 0j, FS, 80.0, 500.0)
