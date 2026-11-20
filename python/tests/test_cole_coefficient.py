"""Cole's coefficient (ADR 0445)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_is_loevingers_h_when_positive_and_never_below_minus_one() -> None:
    rng = np.random.default_rng(208)
    for _ in range(40):
        t = (rng.random(20) < 0.4).astype(float)
        d = (rng.random(20) < 0.5).astype(float)
        t[:2] = [1.0, 0.0]
        d[:2] = [0.0, 1.0]
        c = sf.cole_coefficient(t, d)
        assert -1.0 <= c <= 1.0
        if c >= 0:
            assert c == sf.loevinger_h(t, d)


def test_is_symmetric() -> None:
    t = [1.0, 1.0, 1.0, 0.0, 1.0, 0.0]
    d = [1.0, 0.0, 0.0, 1.0, 0.0, 1.0]
    assert sf.cole_coefficient(t, d) == sf.cole_coefficient(d, t)


def test_rejects_a_constant_record() -> None:
    with pytest.raises(ValueError):
        sf.cole_coefficient([0.0, 1.0], [0.0, 0.0])
