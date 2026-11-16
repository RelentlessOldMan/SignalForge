"""Peak widths (conventions: Spectra, Peak widths; ADR 0138)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

F = np.arange(12.0)
P = np.array([0.5, 3.0, 1.0, 4.0, 3.5, 2.0, 6.0, 0.2, 1.0, 0.3, 2.5, 1.5])


@pytest.mark.parametrize("rel", [0.25, 0.5, 1.0])
def test_scaling_leaves_the_widths(rel: float) -> None:
    base = sf.peak_widths(F, P, rel_height=rel)
    scaled = sf.peak_widths(F, 8 * P, rel_height=rel)
    assert base
    for a, b in zip(base, scaled, strict=True):
        assert b.width == pytest.approx(a.width, rel=1e-12)
        assert b.level == pytest.approx(8 * a.level, rel=1e-12)


def test_crossings_bracket_the_peak() -> None:
    for w in sf.peak_widths(F, P):
        assert w.left <= F[w.index] <= w.right
        assert w.width == w.right - w.left


def test_hann_half_power_width() -> None:
    n, pad = 256, 32
    k = np.arange(n)
    x = np.hanning(n + 1)[:n] * np.exp(2j * np.pi * 20 * k / n)  # periodic Hann at bin 20
    psd = np.abs(np.fft.fft(x, n * pad)) ** 2
    f = np.arange(psd.size) / pad  # in bins of the unpadded length
    main = max(sf.peak_widths(f, psd), key=lambda w: w.level)
    assert main.width == pytest.approx(1.4382, abs=0.01)
