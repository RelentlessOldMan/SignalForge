"""Hopkins' statistic (ADR 0618)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition() -> None:
    rng = np.random.default_rng(618)
    for _ in range(20):
        u = rng.uniform(0.0, 2.0, 25)
        w = rng.uniform(0.0, 2.0, 30)
        got = sf.hopkins_statistic(u, w)
        su = float(np.sum(u**2))
        assert got == pytest.approx(su / (su + float(np.sum(w**2))), rel=1e-14)
        assert sf.hopkins_statistic(3.0 * u, 3.0 * w) == pytest.approx(got, rel=1e-14)
        assert sf.hopkins_statistic(w, u) == pytest.approx(1.0 - got, rel=1e-13)


def test_random_pattern_is_near_one_half() -> None:
    rng = np.random.default_rng(1)
    n = 2000
    pts = rng.uniform(0.0, 1.0, (n, 2))

    def nearest(q: np.ndarray, self_too: bool) -> np.ndarray:
        diff = np.abs(q[:, None, :] - pts[None, :, :])
        diff = np.minimum(diff, 1.0 - diff)
        dist = np.sqrt((diff**2).sum(axis=2))
        if self_too:
            np.fill_diagonal(dist, np.inf)
        return dist.min(axis=1)

    u = nearest(rng.uniform(0.0, 1.0, (300, 2)), False)
    w = nearest(pts[:300], True)
    assert sf.hopkins_statistic(u, w) == pytest.approx(0.5, abs=0.06)


def test_special_cases() -> None:
    assert sf.hopkins_statistic([1.0, 2.0], [2.0, 1.0]) == 0.5
    assert sf.hopkins_statistic([1e300, 1e300], [1e300]) == pytest.approx(2.0 / 3.0)
    assert sf.hopkins_statistic([5e-324], [5e-324]) == 0.5


@pytest.mark.parametrize(
    ("u", "w"),
    [
        ([], [1.0]),
        ([1.0], []),
        ([1.0, -1.0], [1.0]),
        ([1.0, np.nan], [1.0]),
        ([1.0], [np.inf]),
        ([[1.0, 2.0]], [1.0]),
        ([0.0], [1.0]),
        ([1.0], [0.0, 0.0]),
    ],
)
def test_rejects_bad_arguments(u: list[float], w: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.hopkins_statistic(u, w)
