"""Schroeder reverberator (ADR 0295)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

COMBS = [1427, 1601, 1867, 2053]
GAINS = [0.805, 0.827, 0.783, 0.764]


def test_the_tail_decays() -> None:
    x = np.zeros(48000)
    x[0] = 1.0
    y = sf.schroeder_reverb(x, COMBS, GAINS, [347, 113], 0.7, 1.0)
    early = np.sum(y[2000:12000] ** 2)
    late = np.sum(y[38000:48000] ** 2)
    assert 0 < late < 1e-3 * early


def test_the_all_passes_keep_the_comb_energy() -> None:
    x = np.zeros(200000)
    x[0] = 1.0
    combs_only = sf.schroeder_reverb(x, COMBS, GAINS, [], 0.7, 1.0)
    full = sf.schroeder_reverb(x, COMBS, GAINS, [347, 113], 0.7, 1.0)
    assert np.sum(full**2) == pytest.approx(np.sum(combs_only**2), rel=1e-6)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.schroeder_reverb([1j], [3], [0.5], [], 0.5, 0.5)
