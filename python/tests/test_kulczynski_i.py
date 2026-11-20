"""The first Kulczynski coefficient (ADR 0462)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_jaccard_index_as_odds() -> None:
    rng = np.random.default_rng(225)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 1.0]
        d[:2] = [1.0, 0.0]
        v = sf.kulczynski_i(t, d)
        j = sf.jaccard_index(t, d)
        assert v == pytest.approx(j / (1 - j), rel=1e-14)
        assert v == sf.kulczynski_i(d, t)


def test_ignores_shared_zeros() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 1.0, 1.0])
    pad = np.zeros(9)
    padded = sf.kulczynski_i(np.concatenate([t, pad]), np.concatenate([d, pad]))
    assert padded == sf.kulczynski_i(t, d)


def test_rejects_records_that_agree_everywhere() -> None:
    with pytest.raises(ValueError):
        sf.kulczynski_i([1.0, 0.0], [1.0, 0.0])
