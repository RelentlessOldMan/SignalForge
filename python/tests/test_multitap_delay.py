"""Multi-tap delay (ADR 0300)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_a_dense_fir() -> None:
    rng = np.random.default_rng(300)
    x = rng.standard_normal(500)
    taps = np.zeros(31)
    taps[0] = 1.0
    taps[[5, 17, 30]] = [0.7, -0.4, 0.2]
    want = np.convolve(x, taps)[: x.size]
    got = sf.multitap_delay(x, [5, 17, 30], [0.7, -0.4, 0.2])
    assert got == pytest.approx(want, rel=0, abs=1e-12)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.multitap_delay([1j], [1], [0.5])
