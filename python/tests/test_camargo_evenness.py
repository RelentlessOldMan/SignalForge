"""Camargo's evenness (ADR 0533)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_pairwise_gaps() -> None:
    rng = np.random.default_rng(296)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        sh = x / np.sum(x)
        gaps = float(np.sum(np.abs(sh[:, None] - sh[None, :]))) / 2
        e = sf.camargo_evenness(x)
        assert e == pytest.approx(1 - gaps / n, rel=1e-12, abs=1e-14)
        assert 1 / n - 1e-14 <= e <= 1 + 1e-14
        assert sf.camargo_evenness(3.5 * x) == pytest.approx(e, rel=1e-12)
        assert sf.camargo_evenness(x[::-1]) == pytest.approx(e, rel=1e-12)
    assert sf.camargo_evenness([2.0] * 8) == 1.0


@pytest.mark.parametrize("bad", [[], [1.0, -1.0], [0.0, 0.0], [1.0, np.inf], [[1.0, 2.0]]])
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.camargo_evenness(bad)
