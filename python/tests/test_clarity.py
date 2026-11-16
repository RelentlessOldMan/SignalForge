"""Clarity and definition (conventions: Clarity and definition; ADR 0172)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_clarity_and_definition_agree() -> None:
    ir = np.random.default_rng(10).standard_normal(4000) * 0.999 ** np.arange(4000)
    d = sf.definition(ir, 8000.0)
    c50 = sf.clarity(ir, 8000.0, time=0.05)
    assert c50 == pytest.approx(10 * math.log10(d / (1 - d)), rel=1e-12)


def test_a_faster_decay_is_clearer() -> None:
    n = np.arange(8000)
    assert sf.clarity(0.999**n, 8000.0) > sf.clarity(0.9999**n, 8000.0)
