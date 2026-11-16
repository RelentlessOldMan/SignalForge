"""Spectral crest factor (conventions: Spectra, Spectral crest factor; ADR 0125)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

F = np.arange(10.0)


def test_scaling_changes_nothing() -> None:
    p = np.array([0.0, 1.0, 3.0, 2.0, 5.0, 0.5, 0.0, 4.0, 1.0, 0.0])
    want = sf.spectral_crest(F, p)
    for k in (1e-9, 3.0, 1e9):
        got = sf.spectral_crest(F, k * p)
        assert got.crest == pytest.approx(want.crest, rel=1e-12)
        assert got.crest_db == pytest.approx(want.crest_db, rel=1e-12)


def test_tone_in_white_noise() -> None:
    # A periodogram of white noise has exponential bins of mean 1; one tone bin of height h
    # gives peak h over a mean near (n - 1 + h) / n.
    n, h = 512, 1000.0
    p = np.random.default_rng(9).exponential(size=n)
    p[200] = h
    got = sf.spectral_crest(np.arange(float(n)), p)
    assert got.peak == h
    assert got.crest == pytest.approx(h * n / (n - 1 + h), rel=0.06)


def test_crest_is_never_below_one() -> None:
    rng = np.random.default_rng(3)
    for _ in range(50):
        p = rng.random(17) * (rng.random(17) > 0.3)
        if not np.any(p > 0):
            continue
        got = sf.spectral_crest(np.arange(17.0), p)
        assert got.crest >= 1.0
        assert got.crest_db >= -1e-12


def test_flat_is_one() -> None:
    got = sf.spectral_crest(F, np.full(10, 3.5))
    assert (got.crest, got.crest_db) == (1.0, 0.0)
    assert math.isclose(got.mean, 3.5)
