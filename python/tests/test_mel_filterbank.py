"""Mel filterbank (conventions: Mel filterbank; ADR 0155)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf

FS, NFFT = 16000.0, 512


@pytest.mark.parametrize("scale", ["htk", "slaney"])
def test_adjacent_filters_sum_to_one_between_their_peaks(scale: str) -> None:
    w = sf.mel_filterbank(20, NFFT, FS, scale=scale)
    peaks = np.asarray(
        sf.mel_to_hz(np.linspace(0, float(sf.hz_to_mel(FS / 2, scale=scale)), 22), scale=scale)
    )[1:-1]
    bins = np.arange(NFFT // 2 + 1) * FS / NFFT
    between = (bins >= peaks[0]) & (bins <= peaks[-1])
    assert w.sum(axis=0)[between] == pytest.approx(1.0, abs=1e-12)


def test_shape_and_peak_on_an_edge() -> None:
    w = sf.mel_filterbank(4, 40, 4000.0, 0.0, 1000.0, scale="slaney")
    assert w.shape == (4, 21)
    assert w[1, 4] == pytest.approx(1.0)  # the second peak is at 400 Hz, bin 4


def test_area_normalized_rows_have_unit_area() -> None:
    nfft = 1 << 16
    w = sf.mel_filterbank(10, nfft, FS, 300.0, 6000.0, area_normalized=True)
    assert w.sum(axis=1) * FS / nfft == pytest.approx(1.0, rel=1e-3)
