"""The third Sokal-Sneath coefficient (ADR 0461)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_simple_matching_as_odds() -> None:
    rng = np.random.default_rng(224)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[0], d[0] = 1.0, 0.0
        v = sf.sokal_sneath_iii(t, d)
        s = sf.simple_matching_coefficient(t, d)
        assert v == pytest.approx(s / (1 - s), rel=1e-14)
        assert v == sf.sokal_sneath_iii(d, t)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.sokal_sneath_iii(1 - t, 1 - d) == sf.sokal_sneath_iii(t, d)


def test_rejects_records_that_agree_everywhere() -> None:
    with pytest.raises(ValueError):
        sf.sokal_sneath_iii([1.0, 0.0], [1.0, 0.0])
