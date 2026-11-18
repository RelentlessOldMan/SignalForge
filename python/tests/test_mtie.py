"""Maximum time interval error (ADR 0337)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_grows_with_the_window() -> None:
    x = np.cumsum(np.random.default_rng(28).standard_normal(2000)) * 1e-9
    m = sf.mtie(x, 0.01, [1, 10, 100, 1000])
    assert np.all(np.diff(m.values) >= 0)
    assert m.taus == pytest.approx([0.01, 0.1, 1.0, 10.0])


def test_whole_record_is_the_peak_to_peak() -> None:
    x = np.random.default_rng(29).standard_normal(50)
    assert sf.mtie(x, 1.0, [49]).values[0] == np.ptp(x)


def test_rejects_too_large_a_window() -> None:
    with pytest.raises(ValueError):
        sf.mtie([0.0, 1.0, 2.0], 1.0, [3])
