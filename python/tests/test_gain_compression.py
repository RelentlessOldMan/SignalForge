"""Gain compression and P1dB from a drive sweep (conventions: Gain compression; ADR 0112)."""

import math

import numpy as np
import pytest
from numpy.typing import NDArray

from signalforge import gain_compression


def _cubic_sweep(
    a1: float, a3: float, step_db: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    d = np.arange(-60.0, 0.0 + step_db / 2, step_db) + 20 * math.log10(math.sqrt(abs(a1 / a3)))
    amp = 10 ** (d / 20)
    return d, 20 * np.log10(np.abs(a1 * amp + 0.75 * a3 * amp**3))


@pytest.mark.parametrize(("a1", "a3"), [(1.0, -0.1), (10.0, -1.0), (0.5, -3.0)])
def test_a_fine_cubic_sweep_finds_the_textbook_point(a1: float, a3: float) -> None:
    # 1 + (3/4)(a3/a1) A^2 = 10^(-1/20)  =>  A^2 = (4/3)(1 - 10^(-1/20)) |a1/a3|
    x, y = _cubic_sweep(a1, a3, 0.01)
    r = gain_compression(x, y)
    a_1db = math.sqrt(4 / 3 * (1 - 10 ** (-1 / 20)) * abs(a1 / a3))
    assert r.small_signal_gain_db == pytest.approx(20 * math.log10(a1), abs=1e-5)
    assert r.input_point_db == pytest.approx(20 * math.log10(a_1db), abs=1e-4)
    assert r.output_point_db == pytest.approx(
        20 * math.log10(a_1db) + 20 * math.log10(a1) - 1, abs=1e-4
    )


@pytest.mark.parametrize("shift", [-37.0, 0.5, 120.0])
def test_shifting_the_outputs_moves_the_gain_not_the_input_point(shift: float) -> None:
    x, y = _cubic_sweep(10.0, -1.0, 0.5)
    r0 = gain_compression(x, y)
    r = gain_compression(x, y + shift)
    assert r.small_signal_gain_db == pytest.approx(r0.small_signal_gain_db + shift, abs=1e-9)
    assert r.input_point_db == pytest.approx(r0.input_point_db, abs=1e-9)
    assert r.output_point_db == pytest.approx(r0.output_point_db + shift, abs=1e-9)
    assert r.saturated_output_db == pytest.approx(r0.saturated_output_db + shift, abs=1e-9)


def test_a_linear_sweep_never_compresses() -> None:
    x = np.linspace(-40.0, 10.0, 11)
    r = gain_compression(x, x + 12.0, compression_db=0.1)
    assert math.isnan(r.input_point_db) and math.isnan(r.output_point_db)
    np.testing.assert_allclose(r.compression, 0.0, atol=1e-12)
    assert r.saturated_output_db == 22.0


def test_expansion_reads_as_negative_compression() -> None:
    r = gain_compression([-20.0, -10.0, 0.0], [-10.0, 0.5, 9.0])
    np.testing.assert_allclose(r.compression, [0.0, -0.5, 1.0])
    assert r.input_point_db == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("x", "y", "kwargs"),
    [
        ([0.0, 1.0], [0.0], {}),
        ([1.0, 0.0], [0.0, 0.0], {}),
        ([0.0, math.inf], [0.0, 0.0], {}),
        ([0.0, 1.0], [0.0, 0.0], {"compression_db": -1.0}),
        ([0.0, 1.0], [0.0, 0.0], {"compression_db": math.nan}),
        ([0.0, 1.0], [0.0, 0.0], {"linear_points": 3}),
        ([[0.0, 1.0]], [[0.0, 0.0]], {}),
    ],
)
def test_bad_arguments(x: object, y: object, kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        gain_compression(x, y, **kwargs)  # type: ignore[arg-type]
