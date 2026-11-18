"""Feedback FM operator (ADR 0322)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_no_feedback_is_a_sine() -> None:
    y = sf.feedback_fm(8000.0, 300, 123.0, 0.0, 0.6, 0.2)
    t = 123.0 * (np.arange(300) / 8000.0) + 0.2
    assert np.allclose(y, 0.6 * np.sin(2 * np.pi * (t - np.floor(t))), rtol=0, atol=1e-14)


def test_more_feedback_is_brighter() -> None:
    # One second at 8 kHz, 100 Hz: the share of power above the fundamental grows with the
    # feedback, and the wave keeps the fundamental's period.
    def overtones(b: float) -> float:
        p = np.abs(np.fft.rfft(sf.feedback_fm(8000.0, 8000, 100.0, b))) ** 2
        return float(p[150:].sum() / p.sum())

    shares = [overtones(b) for b in (0.0, 0.4, 0.8, 1.2, 1.5)]
    assert shares[0] < 1e-20
    assert shares == sorted(shares)


def test_rejects_too_much_feedback() -> None:
    with pytest.raises(ValueError):
        sf.feedback_fm(8000.0, 4, 1000.0, 1.51)
