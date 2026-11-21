"""The log relative risk (ADR 0509)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_of_the_relative_risk() -> None:
    rng = np.random.default_rng(272)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        v = sf.log_relative_risk(t, d)
        assert v == pytest.approx(math.log(sf.relative_risk(t, d)), rel=1e-14, abs=1e-15)
        assert v / sf.log_relative_risk_standard_error(t, d) == pytest.approx(
            sf.log_relative_risk_wald_z(t, d), rel=1e-13, abs=1e-15
        )


def test_rejects_no_false_negative() -> None:
    with pytest.raises(ValueError):
        sf.log_relative_risk([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0])
