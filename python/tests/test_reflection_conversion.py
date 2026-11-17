"""Reflection coefficients and prediction filters (ADR 0210)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_round_trip_burg_fits() -> None:
    rng = np.random.default_rng(61)
    for x in (rng.standard_normal(300), rng.standard_normal(300) + 1j * rng.standard_normal(300)):
        fit = sf.burg(x, 9)
        assert np.allclose(sf.reflection_to_lpc(fit.reflection), fit.coefficients, atol=1e-12)
        assert np.allclose(sf.lpc_to_reflection(fit.coefficients), fit.reflection, atol=1e-12)


def test_real_in_real_out() -> None:
    assert sf.reflection_to_lpc([0.5, -0.2]).dtype == np.float64
    assert sf.lpc_to_reflection([1.0, 0.3, -0.2]).dtype == np.float64
