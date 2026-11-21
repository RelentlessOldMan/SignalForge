"""The Wald z of the risk difference (ADR 0503)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_risk_difference_over_its_standard_error() -> None:
    rng = np.random.default_rng(266)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 1.0]
        want = sf.risk_difference(t, d) / sf.risk_difference_standard_error(t, d)
        v = sf.risk_difference_wald_z(t, d)
        assert v == pytest.approx(want, rel=1e-13, abs=1e-15)
        assert sf.risk_difference_wald_z(1 - t, d) == pytest.approx(-v, rel=1e-13, abs=1e-15)


def test_rejects_equal_records() -> None:
    with pytest.raises(ValueError):
        sf.risk_difference_wald_z([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0])
