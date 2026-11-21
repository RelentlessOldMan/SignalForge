"""The Wald z of Cohen's h (ADR 0508)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_cohen_h_wald_z_over_its_standard_error() -> None:
    rng = np.random.default_rng(271)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        want = sf.cohen_h(t, d) / sf.cohen_h_standard_error(t, d)
        v = sf.cohen_h_wald_z(t, d)
        assert v == pytest.approx(want, rel=1e-14, abs=1e-15)
        assert sf.cohen_h_wald_z(1 - t, d) == pytest.approx(-v, rel=1e-14, abs=1e-15)


def test_rejects_a_decision_with_no_zero() -> None:
    with pytest.raises(ValueError):
        sf.cohen_h_wald_z([1.0, 0.0, 1.0], [1.0, 1.0, 1.0])
