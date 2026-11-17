"""AR order selection (conventions: AR order selection; ADR 0206)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_picks_the_order_of_an_ar2_process() -> None:
    rng = np.random.default_rng(57)
    w = rng.standard_normal(5000)
    x = np.zeros(5000)
    for i in range(2, 5000):
        x[i] = 1.2 * x[i - 1] - 0.6 * x[i - 2] + w[i]
    s = sf.ar_order_selection(x, 10)
    assert s.aic_order == 2
    assert 2 <= s.fpe_order <= 4


def test_last_error_matches_the_burg_fit() -> None:
    x = np.random.default_rng(58).standard_normal(50) + 1j
    s = sf.ar_order_selection(x, 5)
    assert abs(s.errors[-1] - sf.burg(x, 5).error) <= 1e-12 * s.errors[-1]
