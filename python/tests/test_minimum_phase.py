"""Minimum phase from the cepstrum (conventions: Minimum phase; ADR 0153)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

# Zeros at radii 0.5 to 2, none near the unit circle, so 1024 bins alias far below 1e-12.
X = np.real(np.poly([0.5, -2.0, 1.6j, -1.6j, 0.7 + 0.3j, 0.7 - 0.3j]))


def test_magnitude_is_kept() -> None:
    y = sf.minimum_phase(X, 1024)
    assert np.abs(np.fft.fft(y)) == pytest.approx(np.abs(np.fft.fft(X, 1024)), abs=1e-10)


def test_partial_energies_are_at_least_the_inputs() -> None:
    y = sf.minimum_phase(X, 1024)
    assert np.all(np.cumsum(y[: X.size] ** 2) >= np.cumsum(X**2) - 1e-10)
    assert np.max(np.abs(y[X.size :])) < 1e-10


def test_leading_taps_are_minimum_phase() -> None:
    y = sf.minimum_phase(X, 1024)
    assert np.all(np.abs(np.roots(y[: X.size])) < 1)


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError, match="real"):
        sf.minimum_phase([1.0 + 1j, 0.5])
