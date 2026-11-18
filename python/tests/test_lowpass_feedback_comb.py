"""Damped feedback comb (ADR 0297)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_the_peaks_at_dc_and_nyquist_follow_the_loop_gain() -> None:
    x = np.zeros(4096)
    x[0] = 1.0
    s = np.abs(np.fft.rfft(sf.lowpass_feedback_comb(x, 8, 0.5, 0.5)))
    assert s[0] == pytest.approx(1 / (1 - 0.5), rel=1e-9)
    assert s[-1] == pytest.approx(1 / (1 - 0.5 * 0.5 / 1.5), rel=1e-9)


def test_no_damping_is_the_feedback_comb() -> None:
    x = np.sin(np.arange(300) * 0.37)
    want = sf.comb_filter(x, 7, 0.8, feedback=True)
    assert sf.lowpass_feedback_comb(x, 7, 0.8, 0.0) == pytest.approx(want, rel=0, abs=1e-15)


def test_rejects_complex_samples() -> None:
    with pytest.raises(ValueError):
        sf.lowpass_feedback_comb([1j], 3, 0.5, 0.5)
