"""ERB-spaced frequencies (conventions: ERB-spaced frequencies; ADR 0162)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_ascending_with_exact_endpoints_and_equal_erb_steps() -> None:
    f = sf.erb_space(80.0, 7600.0, 40)
    assert f[0] == 80.0 and f[-1] == 7600.0
    assert np.all(np.diff(f) > 0)
    steps = np.diff(np.asarray(sf.hz_to_erb_rate(f)))
    assert steps == pytest.approx(np.full(39, steps.mean()), rel=1e-10)
