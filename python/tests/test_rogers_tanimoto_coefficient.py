"""The Rogers-Tanimoto coefficient (ADR 0425)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_follows_from_the_simple_matching_coefficient() -> None:
    rng = np.random.default_rng(184)
    for _ in range(20):
        t = (rng.random(30) < 0.5).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        s = sf.simple_matching_coefficient(t, d)
        assert sf.rogers_tanimoto_coefficient(t, d) == pytest.approx(s / (2 - s), rel=1e-14)
        assert sf.rogers_tanimoto_coefficient(t, d) <= s


def test_is_symmetric() -> None:
    t, d = [1.0, 1.0, 0.0, 1.0], [0.0, 1.0, 1.0, 1.0]
    assert sf.rogers_tanimoto_coefficient(t, d) == sf.rogers_tanimoto_coefficient(d, t)


def test_rejects_a_value_other_than_zero_or_one() -> None:
    with pytest.raises(ValueError):
        sf.rogers_tanimoto_coefficient([1.0, 0.5], [1.0, 0.0])
