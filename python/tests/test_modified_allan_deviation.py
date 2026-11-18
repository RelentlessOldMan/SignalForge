"""Modified Allan deviation (ADR 0328)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def _triple_sum(y: np.ndarray, m: int) -> float:
    terms = y.size - 3 * m + 2
    total = 0.0
    for j in range(terms):
        s = sum(y[k + m] - y[k] for i in range(j, j + m) for k in range(i, i + m))
        total += s * s
    return math.sqrt(total / (2 * m**4 * terms))


def test_matches_the_triple_sum() -> None:
    y = np.random.default_rng(12).standard_normal(60)
    got = sf.modified_allan_deviation(y, 1.0, [1, 2, 5, 13, 20]).deviations
    want = [_triple_sum(y, m) for m in (1, 2, 5, 13, 20)]
    assert np.allclose(got, want, rtol=1e-12, atol=0)


def test_one_is_the_allan_deviation() -> None:
    y = np.random.default_rng(13).standard_normal(100)
    a = sf.allan_deviation(y, 0.5, [1]).deviations
    assert sf.modified_allan_deviation(y, 0.5, [1]).deviations == pytest.approx(a, rel=1e-14)


def test_white_phase_noise_falls_faster_than_in_the_allan_deviation() -> None:
    # White phase noise x gives y = diff(x) / tau0: ADEV goes as 1/tau, MDEV as tau^-3/2.
    y = np.diff(np.random.default_rng(14).standard_normal(100001))
    a = sf.allan_deviation(y, 1.0, [4, 64]).deviations
    b = sf.modified_allan_deviation(y, 1.0, [4, 64]).deviations
    assert math.log(a[0] / a[1]) / math.log(16) == pytest.approx(1.0, abs=0.05)
    assert math.log(b[0] / b[1]) / math.log(16) == pytest.approx(1.5, abs=0.05)


def test_rejects_too_large_a_factor() -> None:
    with pytest.raises(ValueError):
        sf.modified_allan_deviation([0.0, 1.0, 2.0, 3.0], 1.0, [2])
