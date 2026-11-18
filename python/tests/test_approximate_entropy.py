"""Approximate entropy (ADR 0333)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_sine_is_more_regular_than_noise() -> None:
    n = np.arange(600)
    sine = np.sin(2 * np.pi * n / 25)
    noise = np.random.default_rng(24).standard_normal(600)
    assert sf.approximate_entropy(sine, 2, 0.2 * sine.std()) < 0.3
    assert sf.approximate_entropy(noise, 2, 0.2) > 1.2


def test_is_at_most_sample_entropy_on_noise() -> None:
    # The self-matches bias ApEn low against SampEn on a short irregular record.
    x = np.random.default_rng(25).standard_normal(300)
    assert sf.approximate_entropy(x, 2, 0.3) < sf.sample_entropy(x, 2, 0.3)


def test_rejects_a_short_record() -> None:
    with pytest.raises(ValueError):
        sf.approximate_entropy([0.0, 1.0, 2.0], 2, 0.5)
