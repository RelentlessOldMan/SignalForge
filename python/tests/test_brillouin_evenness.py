"""The Brillouin evenness (ADR 0547)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _ln_multinomial(counts: list[int]) -> float:
    return math.lgamma(sum(counts) + 1) - sum(math.lgamma(a + 1) for a in counts)


def test_matches_the_log_gamma() -> None:
    rng = np.random.default_rng(310)
    for n in range(2, 30):
        x = rng.integers(0, 30, n).astype(float)
        x[0] += 1.0
        x[1] += 1.0
        counts = [int(a) for a in x if a > 0]
        c, rem = divmod(sum(counts), len(counts))
        even = [c + 1] * rem + [c] * (len(counts) - rem)
        e = sf.brillouin_evenness(x)
        assert e == pytest.approx(_ln_multinomial(counts) / _ln_multinomial(even), rel=1e-10)
        assert 0 < e <= 1 + 1e-12
    assert sf.brillouin_evenness([3.0, 0.0, 3.0, 3.0]) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.parametrize(
    "bad", [[], [4.0], [0.0, 5.0], [1.0, -1.0], [1.5, 2.0], [1e7, 1.0], [1.0, np.inf]]
)
def test_rejects_bad_records(bad: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.brillouin_evenness(bad)
