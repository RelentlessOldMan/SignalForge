"""The Wald z of the log odds ratio (ADR 0498)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_odds_ratio_over_its_standard_error() -> None:
    rng = np.random.default_rng(261)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:4] = [1.0, 1.0, 0.0, 0.0]
        d[:4] = [1.0, 0.0, 1.0, 0.0]
        want = sf.log_odds_ratio(t, d) / sf.log_odds_ratio_standard_error(t, d)
        v = sf.log_odds_ratio_wald_z(t, d)
        assert v == pytest.approx(want, rel=1e-13, abs=1e-15)
        assert sf.log_odds_ratio_wald_z(t, 1 - d) == pytest.approx(-v, rel=1e-13, abs=1e-15)


def test_rejects_a_table_with_a_zero_cell() -> None:
    with pytest.raises(ValueError):
        sf.log_odds_ratio_wald_z([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
