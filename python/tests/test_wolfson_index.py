"""The Wolfson polarization index (ADR 0522)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_its_parts() -> None:
    rng = np.random.default_rng(285)
    for n in range(1, 30):
        x = rng.random(n) * 10 + 0.1
        lc = sf.lorenz_curve(x)
        half = float(np.interp(0.5, np.arange(n + 1) / n, lc))
        g = sf.gini_coefficient(x)
        want = 2 * float(np.mean(x)) / float(np.median(x)) * (1 - 2 * half - g)
        w = sf.wolfson_index(x)
        assert w == pytest.approx(want, rel=1e-12, abs=1e-13)
        assert w >= -1e-13
        assert sf.wolfson_index(3.5 * x) == pytest.approx(w, rel=1e-12, abs=1e-13)
    assert sf.wolfson_index([2.0] * 7) == pytest.approx(0.0, abs=1e-14)


@pytest.mark.parametrize(
    "bad", [[], [1.0, -1.0], [0.0, 0.0], [0.0, 0.0, 0.0, 1.0, 2.0], [1.0, np.inf], [[1.0, 2.0]]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.wolfson_index(bad)
