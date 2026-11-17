"""Yule-Walker AR PSD (conventions: Yule-Walker AR PSD; ADR 0203)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_density_integrates_to_the_mean_power() -> None:
    # the AR fit matches r[0], so the area under the model spectrum is the record's mean power
    x = np.random.default_rng(50).standard_normal(200)
    for one_sided in (True, False):
        d = sf.yule_walker_psd(x, 3.0, 4, nfft=8192, one_sided=one_sided)
        assert abs(float(np.sum(d.psd)) * d.bin_width - float(np.mean(x * x))) < 1e-9


def test_finds_an_ar2_resonance() -> None:
    rng = np.random.default_rng(51)
    e = rng.standard_normal(20000)
    x = np.zeros_like(e)
    r, w = 0.95, 2 * np.pi * 0.2  # poles at 0.95 e^(+-j 0.4 pi): a peak near 0.2 fs
    for i in range(2, x.size):
        x[i] = e[i] + 2 * r * np.cos(w) * x[i - 1] - r * r * x[i - 2]
    d = sf.yule_walker_psd(x, 1.0, 2, nfft=1000)
    assert abs(float(d.frequencies[int(np.argmax(d.psd))]) - 0.2) < 0.01
