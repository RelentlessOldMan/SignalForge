"""Sample entropy (ADR 0326)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_noise_is_less_regular_than_a_sine() -> None:
    rng = np.random.default_rng(8)
    noise = rng.standard_normal(1000)
    sine = np.sin(0.1 * np.arange(1000))
    r = 0.2
    assert sf.sample_entropy(sine, 2, r * float(np.std(sine))) < sf.sample_entropy(noise, 2, r)


def test_uniform_noise_matches_its_closed_form() -> None:
    # i.i.d. uniform on [0, 1): one more sample matches with probability 2r - r^2, so
    # SampEn tends to -ln(2r - r^2).
    x = np.random.default_rng(9).random(3000)
    r = 0.2
    assert sf.sample_entropy(x, 2, r) == pytest.approx(-math.log(2 * r - r * r), rel=0.03)


def test_rejects_a_complex_sample() -> None:
    with pytest.raises(ValueError):
        sf.sample_entropy([0, 1j, 0, 1, 0], 1, 0.5)
