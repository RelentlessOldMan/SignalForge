"""Fades (ADR 0262)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_cosine_fade_lowers_the_click() -> None:
    n = 1024
    x = sf.tone(8000.0, n, 1035.0, complex=False)
    hard = np.abs(np.fft.rfft(np.real(x)))
    soft = np.abs(np.fft.rfft(np.real(sf.fade(x, 128, 128, shape="cosine"))))
    far = slice(300, 513)
    assert np.max(soft[far]) < 1e-2 * np.max(hard[far])


def test_middle_untouched() -> None:
    x = np.random.default_rng(31).standard_normal(100)
    y = sf.fade(x, 10, 20)
    assert np.array_equal(y[10:80], x[10:80])
    assert y[0] == 0 and y[-1] == 0


def test_rejects_unknown_shape() -> None:
    with pytest.raises(ValueError):
        sf.fade([1.0, 2.0], 1, 1, shape="square")
