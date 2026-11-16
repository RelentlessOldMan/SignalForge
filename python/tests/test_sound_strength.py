"""Sound strength (conventions: Sound strength; ADR 0178)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_early_and_late_strength_add_in_energy() -> None:
    ir = np.random.default_rng(14).standard_normal(4000) * 0.999 ** np.arange(4000)
    ref = np.array([0.1])
    early, late = sf.sound_strength(ir[:640], ref), sf.sound_strength(ir[640:], ref)
    total = 10 * math.log10(10 ** (early / 10) + 10 ** (late / 10))
    assert sf.sound_strength(ir, ref) == pytest.approx(total, abs=1e-10)
