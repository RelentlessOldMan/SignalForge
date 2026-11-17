"""PSD confidence interval (conventions: PSD confidence interval; ADR 0201)."""

from __future__ import annotations

import math

import numpy as np

import signalforge as sf
from signalforge import spectral


def test_quantile_round_trips_across_dof_and_tails() -> None:
    # the CDF residual divided by (density * y) is the implied relative error in the quantile
    for nu in (0.5, 1.0, 2.7, 10.0, 37.9, 300.0, 9000.0):
        a = nu / 2
        for p in (1e-6, 0.025, 0.5, 0.975, 1 - 1e-6):
            y = spectral._chi2_quantile(p, nu) / 2
            lo, hi = spectral._gamma_pq(a, y)
            residual = lo - p if p <= 0.5 else (1 - p) - hi
            density = math.exp((a - 1) * math.log(y) - y - math.lgamma(a))
            assert abs(residual) / (density * y) < 1e-12, (nu, p)


def test_coverage_on_white_noise() -> None:
    rng = np.random.default_rng(49)
    k, n = 8, 64
    dof = sf.welch_dof(n, 0, k, window="rectangular")
    inside = total = 0
    for _ in range(100):
        x = rng.standard_normal(n * k)
        psd = sf.welch_psd(x, 2.0, nperseg=n, noverlap=0, window="rectangular").psd[1:-1]
        # unit white noise at fs = 2 has a one-sided PSD of 1 in every interior bin
        ci = sf.psd_confidence_interval(psd, dof, 0.9)
        inside += int(np.sum((ci.lower <= 1.0) & (ci.upper >= 1.0)))
        total += psd.size
    assert abs(inside / total - 0.9) < 0.02
