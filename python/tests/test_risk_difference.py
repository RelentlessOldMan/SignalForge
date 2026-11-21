"""The risk difference (ADR 0501)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_difference_of_the_shares_and_flips_with_the_truth() -> None:
    rng = np.random.default_rng(264)
    for _ in range(30):
        t = (rng.random(25) < 0.5).astype(float)
        d = (rng.random(25) < 0.5).astype(float)
        d[:2] = [1.0, 0.0]
        want = float(np.mean(t[d == 1]) - np.mean(t[d == 0]))
        v = sf.risk_difference(t, d)
        assert v == pytest.approx(want, abs=1e-15)
        assert sf.risk_difference(1 - t, d) == pytest.approx(-v, abs=1e-15)


def test_rejects_a_decision_with_no_zero() -> None:
    with pytest.raises(ValueError):
        sf.risk_difference([1.0, 0.0, 1.0], [1.0, 1.0, 1.0])
