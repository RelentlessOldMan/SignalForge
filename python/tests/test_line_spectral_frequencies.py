"""Line spectral frequencies (conventions: Line spectral frequencies; ADR 0208)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_match_the_unit_circle_roots_of_p_and_q() -> None:
    a = np.poly(
        [
            0.9 * np.exp(0.5j),
            0.9 * np.exp(-0.5j),
            0.7 * np.exp(2.1j),
            0.7 * np.exp(-2.1j),
            -0.4,
            0.2,
        ]
    ).real
    w = sf.line_spectral_frequencies(a)
    ext = np.append(a, 0.0)
    angles = []
    for poly in (ext + ext[::-1], ext - ext[::-1]):
        r = np.roots(poly)
        assert np.allclose(np.abs(r), 1, atol=1e-8)
        angles += [float(np.angle(z)) for z in r if 1e-6 < np.angle(z) < np.pi - 1e-6]
    assert np.allclose(w, sorted(angles), atol=1e-9)


def test_burg_fits_give_interlaced_frequencies() -> None:
    x = np.random.default_rng(59).standard_normal(400)
    w = sf.line_spectral_frequencies(sf.burg(x, 10).coefficients)
    assert w.size == 10 and np.all(np.diff(w) > 0)


def test_complex_coefficients_are_rejected() -> None:
    with pytest.raises(ValueError):
        sf.line_spectral_frequencies([1.0, 0.5j])
