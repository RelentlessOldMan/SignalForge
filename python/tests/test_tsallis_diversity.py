"""The Tsallis diversity of counts (ADR 0568)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition_and_its_special_cases() -> None:
    rng = np.random.default_rng(568)
    x = rng.uniform(0.1, 4.0, 12)
    p = x / np.sum(x)
    for q in [0.3, 0.8, 1.5, 2.0, 3.5]:
        want = (1.0 - float(np.sum(p**q))) / (q - 1.0)
        assert sf.tsallis_diversity(x, q) == pytest.approx(want, rel=1e-12)
    assert sf.tsallis_diversity(x, 0.0) == pytest.approx(11.0, rel=1e-14)
    shannon = -float(np.sum(p * np.log(p)))
    assert sf.tsallis_diversity(x, 1.0) == pytest.approx(shannon, rel=1e-14)
    assert sf.tsallis_diversity(x, 2.0) == pytest.approx(sf.simpson_diversity(x), rel=1e-14)


def test_is_the_tsallis_diversity_shifted() -> None:
    x = [2.0, 0.5, 3.25, 1.0]
    for q in [0.0, 0.5, 1.0, 1.0 + 1e-9, 2.0, 9.0]:
        want = sf.patil_taillie_diversity(x, q - 1.0)
        assert sf.tsallis_diversity(x, q) == pytest.approx(want, rel=1e-13)
    assert sf.tsallis_diversity([0.0, 5.0], 2.0) == 0.0


@pytest.mark.parametrize(
    ("bad", "q"),
    [([], 1.0), ([0.0], 1.0), ([1.0, -1.0], 1.0), ([np.nan], 1.0), ([1.0], -0.5), ([1.0], np.inf)],
)
def test_rejects_bad_arguments(bad: list[float], q: float) -> None:
    with pytest.raises(ValueError):
        sf.tsallis_diversity(bad, q)
