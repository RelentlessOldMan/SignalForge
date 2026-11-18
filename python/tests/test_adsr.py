"""ADSR envelope (ADR 0303)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_stages_join_without_jumps() -> None:
    y = sf.adsr(48000, 480, 4800, 0.6, 9600, 24000)
    assert y[480] == 1.0
    assert np.all(y[5280:24000] == 0.6)
    assert np.max(np.abs(np.diff(y))) <= 1 / 480 + 1e-15
    assert np.all(y[33600:] == 0.0)


def test_rejects_a_float_count() -> None:
    with pytest.raises(ValueError):
        sf.adsr(8, 2.5, 2, 0.5, 2, 5)  # type: ignore[arg-type]
