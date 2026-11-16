"""Cepstral liftering (conventions: Cepstral liftering; ADR 0159)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_keeps_c0_and_peaks_at_half_the_length() -> None:
    out = sf.cepstral_lifter(np.ones(23))
    assert out[0] == 1.0
    assert int(np.argmax(out)) == 11
    assert out[11] == pytest.approx(12.0)


def test_rejects_two_dimensional() -> None:
    with pytest.raises(ValueError):
        sf.cepstral_lifter(np.ones((2, 3)))
