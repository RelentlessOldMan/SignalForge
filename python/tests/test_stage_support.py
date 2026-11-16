"""Stage support (conventions: Stage support; ADR 0179)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_stronger_reflection_raises_the_early_support() -> None:
    ir = np.zeros(48000)
    ir[0] = 1.0
    ir[2400] = 0.1
    weak = sf.stage_support(ir, 48000.0)
    ir[2400] = 0.3
    assert sf.stage_support(ir, 48000.0) - weak == pytest.approx(20 * np.log10(3), abs=1e-12)
