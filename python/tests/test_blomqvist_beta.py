"""Blomqvist's beta (ADR 0375)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_one_for_any_increasing_map() -> None:
    x = np.random.default_rng(93).standard_normal(61)
    assert sf.blomqvist_beta(x, np.exp(x)) == 1.0


def test_matches_the_arcsine_law_for_a_normal_pair() -> None:
    rng = np.random.default_rng(94)
    rho = 0.5
    u = rng.standard_normal(20000)
    v = rho * u + np.sqrt(1 - rho**2) * rng.standard_normal(20000)
    assert sf.blomqvist_beta(u, v) == pytest.approx(2 / np.pi * np.arcsin(rho), abs=0.03)


def test_is_near_zero_for_independent_records() -> None:
    rng = np.random.default_rng(95)
    assert abs(sf.blomqvist_beta(rng.standard_normal(2000), rng.standard_normal(2000))) < 0.1


def test_rejects_every_sample_on_a_median() -> None:
    with pytest.raises(ValueError):
        sf.blomqvist_beta([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
