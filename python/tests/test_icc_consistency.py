"""ICC(3,1) (ADR 0381)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_spearman_brown_step_gives_cronbach_alpha() -> None:
    rng = np.random.default_rng(107)
    rows = rng.standard_normal(25) + rng.standard_normal((4, 25))
    icc = sf.icc_consistency(rows)
    assert 4 * icc / (1 + 3 * icc) == pytest.approx(sf.cronbach_alpha(rows), abs=1e-12)


def test_does_not_change_with_an_offset_per_rater() -> None:
    rng = np.random.default_rng(108)
    rows = rng.standard_normal((3, 20))
    shifted = rows + np.array([[4.0], [-1.0], [0.5]])
    assert sf.icc_consistency(shifted) == pytest.approx(sf.icc_consistency(rows), abs=1e-12)


def test_rejects_ragged_rows() -> None:
    with pytest.raises(ValueError):
        sf.icc_consistency([[1.0, 2.0, 3.0], [1.0, 2.0]])
