"""Autocorrelation of an AR model (ADR 0214)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_levinson_inverts_it() -> None:
    rng = np.random.default_rng(66)
    k = 0.9 * (rng.random(7) - 0.5) + 0.4j * (rng.random(7) - 0.5)
    r = sf.reflection_to_autocorrelation(k, 3.0, 7)
    fit = sf.levinson(r, 7)
    assert np.allclose(fit.reflection, k, atol=1e-12)
    assert abs(fit.error - 3.0 * float(np.prod(1 - np.abs(k) ** 2))) < 1e-12


def test_extension_obeys_the_model() -> None:
    k = [0.5, -0.3, 0.2]
    a = sf.reflection_to_lpc(k)
    r = sf.reflection_to_autocorrelation(k, 1.0, 12)
    for m in range(4, 13):
        assert abs(sum(a[j] * r[m - j] for j in range(4))) < 1e-14
