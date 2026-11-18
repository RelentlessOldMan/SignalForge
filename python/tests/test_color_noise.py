"""Colored noise (ADR 0318)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("exponent", [1.0, 2.0, -1.0, 0.5])
def test_scales_each_bins_power_by_k_to_the_minus_exponent(exponent: float) -> None:
    x = np.random.default_rng(7).standard_normal(1000)
    y = sf.color_noise(x, exponent)
    k = np.arange(1, 501)
    ratio = np.abs(np.fft.rfft(y)[1:]) ** 2 / np.abs(np.fft.rfft(x)[1:]) ** 2
    assert np.allclose(ratio, k**-exponent, rtol=1e-9)
    assert abs(np.mean(y)) < 1e-15


def test_pink_has_equal_power_per_octave() -> None:
    x = np.random.default_rng(3).standard_normal(1 << 16)
    p = np.abs(np.fft.rfft(sf.color_noise(x, 1.0))) ** 2
    octaves = [p[1 << j : 1 << (j + 1)].sum() for j in range(6, 14)]
    assert max(octaves) / min(octaves) < 1.2


@pytest.mark.parametrize("white", [[1j, 2.0], [[1.0, 2.0]], [1.0, float("nan")], [True, False]])
def test_rejects_bad_samples(white: list[object]) -> None:
    with pytest.raises(ValueError):
        sf.color_noise(white, 1.0)  # type: ignore[arg-type]
