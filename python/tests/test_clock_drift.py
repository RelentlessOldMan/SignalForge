"""Sample clock drift against a tone, the fixed offset and its limits (conventions: Channel,
Sample clock drift; ADR 0102)."""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest

import signalforge as sf


def exact_positions(n_in: int, p0: float, p1: float) -> list[float]:
    """t[n+1] = r + (1 + d) t[n] in exact rationals, from the floating-point r and d."""
    r = Fraction(1 + p0 / 1e6)
    d = Fraction((p1 - p0) / 1e6 / (n_in - 1))
    out, t = [], Fraction(0)
    while t <= n_in - 1:
        out.append(float(t))
        t = r + (1 + d) * t
    return out


@pytest.mark.parametrize(("p0", "p1"), [(-1e5, 1e5), (3e4, -2e4), (0.0, 400.0), (5e4, 5.1e4)])
def test_tone_is_read_at_the_drifting_positions(p0: float, p1: float) -> None:
    x = np.exp(2j * math.pi * 0.05 * np.arange(300))
    y = sf.clock_drift(x, p0, p1)
    t = np.array(exact_positions(300, p0, p1))
    assert y.size == t.size
    inner = (t > 16) & (t < 299 - 16)
    # the default kernel's error floor is about 2e-5 at this frequency
    assert np.abs(y - np.exp(2j * math.pi * 0.05 * t))[inner].max() < 5e-5


def test_equal_offsets_are_the_fixed_offset() -> None:
    rng = np.random.default_rng(5)
    x = rng.standard_normal(200) + 1j * rng.standard_normal(200)
    for ppm in (-1e5, -20.0, 0.0, 7e3):
        np.testing.assert_array_equal(sf.clock_drift(x, ppm, ppm), sf.clock_offset(x, ppm))
        np.testing.assert_array_equal(
            sf.clock_drift(x, ppm, ppm, half_width=3), sf.clock_offset(x, ppm, half_width=3)
        )


def test_the_offset_reaches_ppm_end_at_the_last_sample() -> None:
    # the step at the end is 1 + ppm_end/1e6, at the start 1 + ppm_start/1e6
    n_in, p0, p1 = 5000, -4e4, 8e4
    t = np.array(exact_positions(n_in, p0, p1))
    steps = np.diff(t)
    assert steps[0] == pytest.approx(1 + p0 / 1e6, rel=1e-12)
    slope = (p1 - p0) / 1e6 / (n_in - 1)
    assert steps[-1] == pytest.approx(1 + p0 / 1e6 + slope * t[-2], rel=1e-12)
    assert 1 + p1 / 1e6 - steps[-1] < slope * 2
    x = np.arange(n_in, dtype=np.complex128)
    assert sf.clock_drift(x, p0, p1).size == t.size


def test_length_by_hand() -> None:
    # d = 0.01: t_n = (1.01^n - 1)/0.01 <= 10 needs n <= 9.58
    assert sf.clock_drift(np.ones(11), 0.0, 1e5).size == 10


def test_small_inputs() -> None:
    assert sf.clock_drift([], 10.0, -10.0).size == 0
    np.testing.assert_array_equal(sf.clock_drift([2 - 1j], 7e4, -3e4), [2 - 1j])
    # N = 2 reads t = 0 and then t >= 0.9 only if it is at most 1
    assert sf.clock_drift([1.0, 2.0], 1e5, 1e5).size == 1
    assert sf.clock_drift([1.0, 2.0], -1e5, -1e5).size == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ppm_start": 1.000001e5},
        {"ppm_end": -2e5},
        {"ppm_start": math.nan},
        {"ppm_end": math.inf},
        {"half_width": 0},
        {"half_width": 2.0},
        {"ppm_start": True},
    ],
)
def test_bad_arguments(kwargs: dict[str, object]) -> None:
    args: dict[str, object] = {"ppm_start": 10.0, "ppm_end": 20.0} | kwargs
    with pytest.raises(ValueError):
        sf.clock_drift(np.ones(4), **args)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        sf.clock_drift(np.ones((2, 2)), 1.0, 2.0)
