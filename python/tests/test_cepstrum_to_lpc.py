"""Cepstrum to prediction filter (ADR 0222)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_inverts_lpc_cepstrum() -> None:
    a = sf.reflection_to_lpc([0.6 + 0.2j, -0.4, 0.3j, 0.5, -0.2 - 0.1j])
    c = sf.lpc_cepstrum(a, 0.7, 12)
    assert np.allclose(sf.cepstrum_to_lpc(c, 5), a, atol=1e-12)
    assert abs(np.exp(2 * c[0]) - 0.7) < 1e-12


def test_real_stays_real() -> None:
    assert sf.cepstrum_to_lpc([0.0, 0.5], 1).dtype == np.float64
