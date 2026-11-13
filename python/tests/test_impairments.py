"""IQ imbalance and DC offset: the image a tone gets, the Q branch's phase, and the offset's
mean (conventions: Channel, IQ imbalance, Image rejection, DC offset)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize(
    ("gain_db", "phase"),
    [(0.5, 0.0), (0.0, 0.03), (-1.0, -0.2), (2.0, 1.0), (0.1, math.radians(1))],
)
def test_a_tones_image_matches_the_image_rejection(gain_db: float, phase: float) -> None:
    n, k = 64, 5
    x = np.exp(2j * np.pi * k * np.arange(n) / n)
    spectrum = np.fft.fft(sf.iq_imbalance(x, gain_db, phase))
    measured = 10 * math.log10(abs(spectrum[k]) ** 2 / abs(spectrum[n - k]) ** 2)
    assert measured == pytest.approx(sf.iq_image_rejection_db(gain_db, phase), abs=1e-9)
    others = np.delete(spectrum, [k, n - k])
    assert np.max(np.abs(others)) < 1e-12 * n


def test_the_q_branch_is_advanced_and_scaled() -> None:
    theta = np.linspace(0, 2 * np.pi, 37)
    g, phase = 10 ** (1.5 / 20), 0.3
    y = sf.iq_imbalance(np.exp(1j * theta), 1.5, phase)
    np.testing.assert_allclose(y.real, np.cos(theta), atol=1e-15)
    np.testing.assert_allclose(y.imag, g * np.sin(theta + phase), atol=1e-14)


def test_no_imbalance_is_the_identity_and_has_no_image() -> None:
    x = np.array([0.3 - 1.2j, 2.0, -1j])
    np.testing.assert_array_equal(sf.iq_imbalance(x, 0.0, 0.0), x)
    assert sf.iq_image_rejection_db(0.0, 0.0) == math.inf


def test_image_rejection_does_not_depend_on_the_sign_of_the_gain_error() -> None:
    for phase in (0.0, 0.1, -0.4):
        assert sf.iq_image_rejection_db(1.2, phase) == pytest.approx(
            sf.iq_image_rejection_db(-1.2, phase), abs=1e-12
        )


def test_dc_offset_moves_the_mean() -> None:
    x = np.exp(2j * np.pi * np.arange(16) / 16)
    y = sf.dc_offset(x, 0.25 - 0.5j)
    assert np.mean(y) == pytest.approx(0.25 - 0.5j, abs=1e-15)
    assert y.dtype == np.complex128
    assert sf.dc_offset([1.0, 2.0], 1)[1] == 3


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.iq_imbalance([1j], math.nan, 0.0),
        lambda: sf.iq_imbalance([1j], 0.0, math.inf),
        lambda: sf.iq_imbalance([1j], 7000.0, 0.0),
        lambda: sf.iq_imbalance([[1j]], 0.0, 0.0),
        lambda: sf.iq_image_rejection_db(0.0, math.nan),
        lambda: sf.dc_offset([1j], complex(math.inf, 0)),
        lambda: sf.dc_offset([[1j]], 0),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
