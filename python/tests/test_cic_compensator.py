"""CIC droop compensator (ADR 0232)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_flattens_the_cic_passband_on_the_grid() -> None:
    r, n, t = 8, 4, 31
    h = sf.cic_compensator(r, n, t, 0.25, 1.0)
    taps = sf.cic_taps(r, n)
    c = (t - 1) // 2
    for j in range(int(0.25 * t) + 1):
        f = j / t
        cic = abs(np.sum(taps * np.exp(-2j * np.pi * f / r * np.arange(taps.size)))) / r**n
        comp = np.sum(h * np.exp(-2j * np.pi * f * (np.arange(t) - c)))
        assert abs(cic * comp - 1.0) < 1e-10


def test_is_symmetric() -> None:
    h = sf.cic_compensator(5, 3, 25, 0.4, 1.0)
    assert np.allclose(h, h[::-1], rtol=0, atol=1e-15)
