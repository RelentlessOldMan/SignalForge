"""MFCC (conventions: MFCC; ADR 0157)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_scaling_the_power_changes_only_c0() -> None:
    w = sf.mel_filterbank(24, 512, 16000.0, 100.0, 7000.0)
    p = np.random.default_rng(3).uniform(0.5, 2.0, 257)
    a, b = sf.mfcc(p, w, 13), sf.mfcc(9.0 * p, w, 13)
    assert b[0] - a[0] == pytest.approx(math.sqrt(24) * math.log(9.0), rel=1e-12)
    assert b[1:] == pytest.approx(a[1:], abs=1e-12)


def test_matches_dct_of_log_bands() -> None:
    w = sf.mel_filterbank(10, 64, 8000.0, scale="slaney")
    p = np.ones(33)
    bands = np.maximum(w @ p, 1e-10)
    assert sf.mfcc(p, w, 10) == pytest.approx(sf.dct(np.log(bands)), abs=1e-12)
