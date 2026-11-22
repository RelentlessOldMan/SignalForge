"""Hill evenness (ADR 0564)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_the_hill_number_over_the_kinds() -> None:
    rng = np.random.default_rng(564)
    x = rng.uniform(0.1, 4.0, 12)
    x[3] = 0.0
    for q in [0.0, 0.5, 1.0, 1.0001, 2.0, 7.0]:
        want = sf.hill_number(x, q) / 11
        assert sf.hill_evenness(x, q) == pytest.approx(want, rel=1e-14)
    assert sf.hill_evenness(x, 0.0) == 1.0


def test_bounds() -> None:
    assert sf.hill_evenness([3.0, 3.0, 3.0], 2.0) == pytest.approx(1.0, rel=1e-14)
    e = sf.hill_evenness([1e6, 1.0, 1.0, 1.0], 2.0)
    assert 0.25 < e < 0.2501


@pytest.mark.parametrize(("bad", "q"), [([], 1.0), ([0.0], 1.0), ([1.0, -1.0], 1.0), ([1.0], -1.0)])
def test_rejects_bad_arguments(bad: list[float], q: float) -> None:
    with pytest.raises(ValueError):
        sf.hill_evenness(bad, q)
