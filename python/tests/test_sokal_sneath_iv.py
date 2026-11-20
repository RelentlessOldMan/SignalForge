"""The fourth Sokal-Sneath coefficient (ADR 0459)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_symmetric_and_half_the_sum_of_two_balanced_accuracies() -> None:
    rng = np.random.default_rng(222)
    for _ in range(30):
        t = (rng.random(25) < 0.4).astype(float)
        d = (rng.random(25) < 0.6).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [1.0, 0.0]
        v = sf.sokal_sneath_iv(t, d)
        want = (sf.balanced_accuracy(t, d) + sf.balanced_accuracy(d, t)) / 2
        assert v == pytest.approx(want, rel=1e-14)
        assert v == pytest.approx(sf.sokal_sneath_iv(d, t), rel=1e-15)


def test_is_unchanged_when_both_records_are_flipped() -> None:
    t = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0])
    d = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    assert sf.sokal_sneath_iv(1 - t, 1 - d) == pytest.approx(sf.sokal_sneath_iv(t, d), rel=1e-15)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.sokal_sneath_iv([1.0, 1.0], [1.0, 0.0])
