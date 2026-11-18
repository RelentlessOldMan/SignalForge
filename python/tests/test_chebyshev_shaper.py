"""Chebyshev waveshaper (ADR 0321)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_full_scale_cosine_gives_the_weights_as_harmonics() -> None:
    n = 1024
    x = np.cos(2 * np.pi * 8 * np.arange(n) / n)
    w = [0.2, 1.0, -0.5, 0.25, 0.0, 0.125]
    s = np.fft.rfft(sf.chebyshev_shaper(x, w)) / n
    assert s[0].real == pytest.approx(0.2, abs=1e-12)
    for k in range(1, len(w)):
        assert 2 * s[8 * k].real == pytest.approx(w[k], abs=1e-12)
    rest = np.delete(s, [8 * k for k in range(len(w))])
    assert np.max(np.abs(rest)) < 1e-12


def test_matches_numpy_chebval() -> None:
    x = np.linspace(-1, 1, 101)
    w = np.random.default_rng(2).standard_normal(9)
    ref = np.polynomial.chebyshev.chebval(x, w)
    assert np.allclose(sf.chebyshev_shaper(x, w), ref, rtol=0, atol=1e-13)


@pytest.mark.parametrize(("x", "w"), [([1.5], [1.0]), ([0.5j], [1.0]), ([0.5], [1j])])
def test_rejects_bad_samples_or_weights(x: list[complex], w: list[complex]) -> None:
    with pytest.raises(ValueError):
        sf.chebyshev_shaper(x, w)
