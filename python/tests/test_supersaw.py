"""Supersaw (ADR 0316)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_one_voice_is_the_polyblep_sawtooth() -> None:
    y = sf.supersaw(8000.0, 100, 321.0, 40.0, 1, 0.7)
    assert np.allclose(y, sf.polyblep_sawtooth(8000.0, 100, 321.0, 0.7), rtol=0, atol=1e-15)


def test_the_voices_sit_at_their_detuned_pitches() -> None:
    # Two seconds at 8 kHz: 0.5 Hz bins. Five voices over +-100 cents around 500 Hz, with a
    # Hann window so each line stays within a bin or two of its frequency.
    y = sf.supersaw(8000.0, 16000, 500.0, 100.0, 5)
    s = np.abs(np.fft.rfft(y * np.hanning(y.size)))
    bins = np.fft.rfftfreq(16000, 1 / 8000)
    for c in (-100.0, -50.0, 0.0, 50.0, 100.0):
        near = np.abs(bins - 500.0 * 2 ** (c / 1200)) <= 1.0
        assert s[near].max() > 0.5 * s.max()
    gap = np.abs(bins - 500.0 * 2 ** (75 / 1200)) <= 1.0
    assert s[gap].max() < 0.1 * s.max()


@pytest.mark.parametrize(
    ("voices", "detune"), [(0, 10.0), (True, 10.0), (3, -1.0), (3, float("nan"))]
)
def test_rejects_bad_voices_or_detune(voices: int, detune: float) -> None:
    with pytest.raises(ValueError):
        sf.supersaw(8000.0, 4, 1000.0, detune, voices)
