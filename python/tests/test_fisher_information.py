"""Fisher information (ADR 0351)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_is_more_ordered_than_noise() -> None:
    # A sine has rank 2 in any embedding; white noise spreads over all of it.
    sine = np.sin(2 * np.pi * np.arange(500) / 23)
    noise = np.random.default_rng(57).standard_normal(500)
    assert sf.fisher_information(sine, 6) > sf.fisher_information(noise, 6)


def test_a_rank_one_embedding_is_one() -> None:
    # A constant has one singular value: (0 - 1)^2 / 1, and the zero terms count 0.
    assert sf.fisher_information(np.full(20, 3.0), 4) == pytest.approx(1.0, abs=1e-12)


def test_rejects_all_zero() -> None:
    with pytest.raises(ValueError):
        sf.fisher_information(np.zeros(8), 2)
