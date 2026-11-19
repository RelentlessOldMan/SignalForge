"""Bartels rank test (ADR 0363)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_iid_noise_has_a_small_z() -> None:
    z = [sf.bartels_rank_test(np.random.default_rng(s).standard_normal(300)).z for s in range(300)]
    assert abs(np.mean(z)) < 0.2
    assert np.std(z) == pytest.approx(1.0, abs=0.15)


def test_is_unchanged_by_a_monotone_map() -> None:
    x = np.random.default_rng(71).standard_normal(100)
    assert sf.bartels_rank_test(np.exp(x)) == sf.bartels_rank_test(x)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.bartels_rank_test([1.0, 1.0, 1.0])
