"""The Braun-Blanquet coefficient (ADR 0440)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_overlap_coefficient_scaled_by_the_count_ratio() -> None:
    rng = np.random.default_rng(203)
    for _ in range(20):
        t = (rng.random(30) < 0.4).astype(float)
        d = (rng.random(30) < 0.5).astype(float)
        t[0] = d[1] = 1.0
        nt, nd = np.sum(t), np.sum(d)
        want = sf.overlap_coefficient(t, d) * min(nt, nd) / max(nt, nd)
        assert sf.braun_blanquet_coefficient(t, d) == pytest.approx(want, rel=1e-14)
        assert sf.braun_blanquet_coefficient(t, d) <= sf.ochiai_coefficient(t, d) + 1e-15


def test_is_symmetric() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 1.0, 0.0]
    d = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0]
    assert sf.braun_blanquet_coefficient(t, d) == sf.braun_blanquet_coefficient(d, t)


def test_rejects_two_records_of_zeros() -> None:
    with pytest.raises(ValueError):
        sf.braun_blanquet_coefficient([0.0, 0.0], [0.0, 0.0])
