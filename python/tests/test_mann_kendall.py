"""Mann-Kendall trend test (ADR 0364)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_iid_noise_has_a_small_z() -> None:
    z = [sf.mann_kendall(np.random.default_rng(s).standard_normal(100)).z for s in range(300)]
    assert abs(np.mean(z)) < 0.2
    assert np.std(z) == pytest.approx(1.0, abs=0.15)


def test_reversing_negates_s() -> None:
    x = np.random.default_rng(72).standard_normal(80)
    assert sf.mann_kendall(x[::-1]).s == -sf.mann_kendall(x).s


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.mann_kendall([1.0, 1.0])
