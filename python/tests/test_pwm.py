"""Pulse-width modulation (ADR 0312)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_a_constant_duty_is_the_naive_square() -> None:
    y = sf.pwm(np.full(200, 0.3), 8000.0, 123.0, 0.7, 0.2)
    assert np.array_equal(y, sf.square(8000.0, 200, 123.0, 0.3, 0.7, 0.2))


def test_the_mean_follows_a_slow_duty() -> None:
    # 100 Hz at 8 kHz, 80 samples a cycle; the duty steps once a second.
    d = np.repeat([0.25, 0.75], 8000)
    y = sf.pwm(d, 8000.0, 100.0, 1.0, 1 / 160)
    assert np.mean(y[:8000]) == pytest.approx(2 * 0.25 - 1)
    assert np.mean(y[8000:]) == pytest.approx(2 * 0.75 - 1)


def test_an_empty_duty_gives_an_empty_output() -> None:
    assert sf.pwm([], 8000.0, 1000.0).shape == (0,)


@pytest.mark.parametrize("bad", [[0.5, float("nan")], [[0.5]], [0.5, 2.0]])
def test_rejects_a_bad_duty(bad: list[float] | list[list[float]]) -> None:
    with pytest.raises(ValueError):
        sf.pwm(bad, 8000.0, 1000.0)
