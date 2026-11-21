"""The Wald z of the log relative risk (ADR 0500)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_the_log_relative_risk_over_its_standard_error() -> None:
    rng = np.random.default_rng(263)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        t[:3] = [1.0, 1.0, 0.0]
        d[:3] = [1.0, 0.0, 0.0]
        want = math.log(sf.relative_risk(t, d)) / sf.log_relative_risk_standard_error(t, d)
        v = sf.log_relative_risk_wald_z(t, d)
        assert v == pytest.approx(want, rel=1e-13, abs=1e-15)


def test_rejects_records_where_every_truth_is_one() -> None:
    with pytest.raises(ValueError):
        sf.log_relative_risk_wald_z([1.0, 1.0, 1.0], [1.0, 0.0, 1.0])
