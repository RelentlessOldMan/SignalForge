"""Thiran allpass (ADR 0227)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def _response(a: np.ndarray, w: np.ndarray) -> np.ndarray:
    z = np.exp(-1j * np.outer(w, np.arange(a.size)))
    return np.asarray((z @ a[::-1]) / (z @ a))


def test_unit_magnitude_and_dc_group_delay() -> None:
    for order, d in ((1, 0.3), (2, 1.6), (4, 4.2), (5, 4.5)):
        a = sf.thiran_allpass(d, order)
        w = np.linspace(0.01, 3.0, 50)
        assert np.allclose(np.abs(_response(a, w)), 1.0, atol=1e-12)
        h = 1e-4
        phase = np.unwrap(np.angle(_response(a, np.array([h, 2 * h]))))
        assert abs(-(phase[1] - phase[0]) / h - d) < 1e-6


def test_stable() -> None:
    a = sf.thiran_allpass(3.3, 4)
    assert np.all(np.abs(np.roots(a)) < 1)
