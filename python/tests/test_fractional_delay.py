"""Fractional delay: tones come through delayed as theory says, whole-sample delays are exact
shifts (conventions: Channel, Fractional delay)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(("freq", "bound"), [(0.05, 5e-5), (0.25, 5e-5), (0.4, 3e-4)])
def test_a_tone_is_delayed(freq: float, bound: float) -> None:
    n = np.arange(400)
    for d in (0.37, 3.5, -2.8):
        y = sf.fractional_delay(np.exp(2j * np.pi * freq * n), d)
        want = np.exp(2j * np.pi * freq * (n - d))
        assert np.abs(y - want)[50:350].max() < bound


def test_whole_sample_delays_are_exact() -> None:
    x = np.random.default_rng(5).standard_normal(64)
    for d in (0, 1, 7, -3):
        want = np.zeros(64, complex)
        if d >= 0:
            want[d:] = x[: 64 - d]
        else:
            want[:d] = x[-d:]
        np.testing.assert_array_equal(sf.fractional_delay(x, float(d), half_width=5), want)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.fractional_delay([[1.0]], 0.5),
        lambda: sf.fractional_delay([1.0], float("nan")),
        lambda: sf.fractional_delay([1.0], 0.5, half_width=0),
        lambda: sf.fractional_delay([1.0], 0.5, half_width=2.0),  # type: ignore[arg-type]
        lambda: sf.fractional_delay([1.0], True),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
