"""A and C weighting filters (conventions: Weighting filters; ADR 0165)."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest
from numpy.typing import ArrayLike, NDArray

import signalforge as sf

Design = Callable[[float], NDArray[np.float64]]
Curve = Callable[[ArrayLike], "NDArray[np.float64] | float"]


@pytest.mark.parametrize("fs", [8000.0, 48000.0, 192000.0])
@pytest.mark.parametrize(
    ("design", "curve"),
    [(sf.a_weighting_sos, sf.a_weighting), (sf.c_weighting_sos, sf.c_weighting)],
)
def test_response_is_the_curve_at_the_warped_frequency(
    fs: float, design: Design, curve: Curve
) -> None:
    sos = design(fs)
    f = np.linspace(10.0, 0.45 * fs, 200)
    got = 20 * np.log10(np.abs(sf.sos_response(sos, f, fs)))

    def warped(x: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.asarray(fs / np.pi * np.tan(np.pi * x / fs))

    want = np.asarray(curve(warped(f))) - float(curve(warped(np.array(1000.0))))
    assert got == pytest.approx(want, rel=1e-9, abs=1e-9)
    assert abs(sf.sos_response(sos, [1000.0], fs)[0]) == pytest.approx(1.0, abs=1e-12)
