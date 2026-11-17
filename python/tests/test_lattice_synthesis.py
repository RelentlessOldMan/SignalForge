"""Lattice synthesis filter (conventions: Lattice synthesis filter; ADR 0212)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_inverts_the_analysis_lattice() -> None:
    rng = np.random.default_rng(64)
    x = rng.standard_normal(300) + 1j * rng.standard_normal(300)
    k = 0.9 * (rng.random(7) - 0.5) + 0.4j * (rng.random(7) - 0.5)
    y = sf.lattice_synthesis(sf.lattice_filter(x, k), k)
    assert np.allclose(y, x, atol=1e-10)


def test_real_inputs_give_a_real_array() -> None:
    assert sf.lattice_synthesis([1.0, 0.0], [0.5]).dtype == np.float64
