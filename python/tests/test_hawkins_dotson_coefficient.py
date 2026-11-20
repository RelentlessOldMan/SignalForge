"""The Hawkins-Dotson coefficient (ADR 0454)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_mean_of_the_jaccard_indices_of_the_ones_and_the_zeros() -> None:
    rng = np.random.default_rng(217)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        want = (sf.jaccard_index(t, d) + sf.jaccard_index(1 - t, 1 - d)) / 2
        assert sf.hawkins_dotson_coefficient(t, d) == pytest.approx(want, rel=1e-15)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.hawkins_dotson_coefficient(1 - t, 1 - d) == sf.hawkins_dotson_coefficient(t, d)


def test_rejects_two_records_all_one() -> None:
    with pytest.raises(ValueError):
        sf.hawkins_dotson_coefficient([1.0, 1.0], [1.0, 1.0])
