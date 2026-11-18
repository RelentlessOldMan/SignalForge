"""Tilt EQ (ADR 0283)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_gains_at_dc_pivot_and_nyquist() -> None:
    sos = sf.tilt_eq(800.0, 9.0, 48000.0)
    h = np.abs(sf.sos_response(sos, [0.0, 800.0, 24000.0], 48000.0))
    db = 20 * np.log10(h)
    assert db == pytest.approx([-4.5, 0.0, 4.5], abs=1e-9)


def test_opposite_tilts_cancel() -> None:
    f = np.linspace(0, 4000, 9)
    up = sf.sos_response(sf.tilt_eq(500.0, 7.0, 8000.0), f, 8000.0)
    down = sf.sos_response(sf.tilt_eq(500.0, -7.0, 8000.0), f, 8000.0)
    assert np.abs(up * down) == pytest.approx(np.ones(9), abs=1e-12)


def test_rejects_frequency_at_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.tilt_eq(4.0, 3.0, 8.0)
