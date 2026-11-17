"""LSF to prediction filter (conventions: LSF to prediction filter; ADR 0209)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_round_trips_a_burg_fit() -> None:
    x = np.random.default_rng(60).standard_normal(500)
    for order in (1, 2, 7, 12):
        a = sf.burg(x, order).coefficients
        assert np.allclose(sf.lsf_to_lpc(sf.line_spectral_frequencies(a)), a, atol=1e-10)


def test_interpolated_frequencies_stay_minimum_phase() -> None:
    w1 = np.array([0.2, 0.5, 1.1, 1.6, 2.4, 2.9])
    w2 = np.array([0.4, 0.6, 1.3, 2.0, 2.2, 3.0])
    a = sf.lsf_to_lpc(0.5 * (w1 + w2))
    assert np.all(np.abs(np.roots(a)) < 1)
