"""The Patil-Taillie diversity (ADR 0565)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_matches_the_definition_and_its_special_cases() -> None:
    rng = np.random.default_rng(565)
    x = rng.uniform(0.1, 4.0, 12)
    p = x / np.sum(x)
    for b in [-0.7, -0.2, 0.3, 1.0, 2.5]:
        want = (1.0 - float(np.sum(p ** (b + 1.0)))) / b
        assert sf.patil_taillie_diversity(x, b) == pytest.approx(want, rel=1e-12)
    assert sf.patil_taillie_diversity(x, -1.0) == pytest.approx(11.0, rel=1e-14)
    assert sf.patil_taillie_diversity(x, 0.0) == pytest.approx(
        -float(np.sum(p * np.log(p))), rel=1e-14
    )
    assert sf.patil_taillie_diversity(x, 1.0) == pytest.approx(sf.simpson_diversity(x), rel=1e-14)


def test_is_continuous_at_zero() -> None:
    x = [2.0, 0.5, 3.25, 1.0]
    h = sf.patil_taillie_diversity(x, 0.0)
    for b in [-1e-9, 1e-9]:
        assert sf.patil_taillie_diversity(x, b) == pytest.approx(h, rel=1e-8)
    assert sf.patil_taillie_diversity([0.0, 5.0], 2.0) == 0.0
    assert math.isfinite(sf.patil_taillie_diversity(x, 1e300))


@pytest.mark.parametrize(
    ("bad", "b"),
    [([], 1.0), ([0.0], 1.0), ([1.0, -1.0], 1.0), ([np.nan], 1.0), ([1.0], -1.5), ([1.0], np.inf)],
)
def test_rejects_bad_arguments(bad: list[float], b: float) -> None:
    with pytest.raises(ValueError):
        sf.patil_taillie_diversity(bad, b)
