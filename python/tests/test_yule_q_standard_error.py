"""The standard error of Yule's Q (ADR 0495)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_delta_method_error_of_yule_q() -> None:
    rng = np.random.default_rng(258)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:4] = [1.0, 1.0, 0.0, 0.0]
        d[:4] = [1.0, 0.0, 1.0, 0.0]
        q = sf.yule_q(t, d)
        want = 0.5 * (1.0 - q * q) * sf.log_odds_ratio_standard_error(t, d)
        v = sf.yule_q_standard_error(t, d)
        assert v == pytest.approx(want, rel=1e-13)
        assert sf.yule_q_standard_error(d, t) == v


def test_rejects_a_table_with_a_zero_cell() -> None:
    with pytest.raises(ValueError):
        sf.yule_q_standard_error([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
