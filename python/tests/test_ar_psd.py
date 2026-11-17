"""AR model PSD (ADR 0223)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_burg_psd_of_the_same_model() -> None:
    rng = np.random.default_rng(5)
    x = rng.standard_normal(300)
    fit = sf.burg(x, 4)
    burg = sf.burg_psd(x, 8.0, 4, nfft=64)
    model = sf.ar_psd(fit.coefficients, fit.error, 8.0, 64)
    assert np.allclose(model.psd, burg.psd, rtol=1e-12)
    assert np.allclose(model.frequencies, burg.frequencies)


def test_integrates_to_r0() -> None:
    a = sf.reflection_to_lpc([0.5, -0.3, 0.2])
    d = sf.ar_psd(a, 1.3, 10.0, 4096, one_sided=False)
    r0 = sf.lpc_to_autocorrelation(a, 1.3, 0)[0]
    assert abs(np.sum(d.psd) * d.bin_width - r0) < 1e-10


def test_one_sided_needs_real() -> None:
    with pytest.raises(ValueError):
        sf.ar_psd([1.0, 0.5j], 1.0, 1.0, 8, one_sided=True)
