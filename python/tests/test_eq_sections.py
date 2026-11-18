"""Shelving and peaking EQ sections (ADR 0282)."""

from __future__ import annotations

import numpy as np
import pytest
from numpy.typing import NDArray

import signalforge as sf


def _db(sos: NDArray[np.float64], f: float, fs: float) -> float:
    return float(20 * np.log10(np.abs(sf.sos_response(sos, [f], fs)[0])))


def test_peaking_gain_at_centre_and_ends() -> None:
    sos = sf.peaking_eq(1000.0, 7.5, 2.0, 48000.0)
    assert _db(sos, 1000.0, 48000.0) == pytest.approx(7.5, abs=1e-9)
    assert _db(sos, 0.0, 48000.0) == pytest.approx(0.0, abs=1e-9)
    assert _db(sos, 24000.0, 48000.0) == pytest.approx(0.0, abs=1e-9)


def test_shelves_reach_their_gain() -> None:
    lo = sf.low_shelf(300.0, -8.0, 0.7071, 48000.0)
    hi = sf.high_shelf(6000.0, 5.0, 0.7071, 48000.0)
    assert _db(lo, 0.0, 48000.0) == pytest.approx(-8.0, abs=1e-9)
    assert _db(lo, 24000.0, 48000.0) == pytest.approx(0.0, abs=1e-9)
    assert _db(hi, 0.0, 48000.0) == pytest.approx(0.0, abs=1e-9)
    assert _db(hi, 24000.0, 48000.0) == pytest.approx(5.0, abs=1e-9)


def test_section_shape_and_filtering() -> None:
    sos = sf.low_shelf(100.0, 6.0, 1.0, 8000.0)
    assert sos.shape == (1, 6)
    y = sf.IirFilter(sos).process(np.ones(20000))
    assert y[-1] == pytest.approx(10 ** (6 / 20), rel=1e-6)


def test_rejects_frequency_at_nyquist() -> None:
    with pytest.raises(ValueError):
        sf.peaking_eq(4.0, 3.0, 1.0, 8.0)
