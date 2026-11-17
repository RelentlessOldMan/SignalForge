"""Transfer function H2 (conventions: Transfer function (H2); ADR 0195)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_h1_over_h2_is_the_coherence() -> None:
    rng = np.random.default_rng(43)
    x = rng.standard_normal(4096)
    y = np.convolve(x, [0.6, 0.2])[: x.size] + 0.3 * rng.standard_normal(x.size)
    h1 = sf.transfer_function(x, y, 1.0, nperseg=128).response
    h2 = sf.transfer_function_h2(x, y, 1.0, nperseg=128).response
    c = sf.coherence(x, y, 1.0, nperseg=128).values
    assert np.allclose(h1 / h2, c)
