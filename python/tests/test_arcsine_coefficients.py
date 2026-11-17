"""Inverse sine coefficients (ADR 0216)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_round_trip() -> None:
    k = np.linspace(-0.98, 0.98, 41)
    assert np.allclose(sf.arcsine_to_reflection(sf.reflection_to_arcsine(k)), k, atol=1e-15)


def test_complex_is_rejected() -> None:
    with pytest.raises(ValueError):
        sf.reflection_to_arcsine([0.5j])
    with pytest.raises(ValueError):
        sf.arcsine_to_reflection([1j])
