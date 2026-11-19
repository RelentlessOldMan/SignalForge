"""Scott's pi (ADR 0384)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_fleiss_kappa_with_two_raters() -> None:
    rng = np.random.default_rng(112)
    a = rng.integers(0, 4, 80).astype(float)
    b = np.where(rng.random(80) < 0.5, a, rng.integers(0, 2, 80)).astype(float)
    counts = np.stack([(a == c).astype(float) + (b == c) for c in range(4)], axis=1)
    assert sf.scott_pi(a, b) == pytest.approx(sf.fleiss_kappa(counts), abs=1e-14)


def test_is_at_most_cohen_kappa() -> None:
    # Pooling the rates can only raise the chance term, so pi never exceeds kappa.
    rng = np.random.default_rng(113)
    a = rng.integers(0, 3, 200).astype(float)
    b = np.where(rng.random(200) < 0.7, a, 0.0)
    assert sf.scott_pi(a, b) <= sf.cohen_kappa(a, b)


def test_rejects_one_shared_label() -> None:
    with pytest.raises(ValueError):
        sf.scott_pi([1.0, 1.0], [1.0, 1.0])
