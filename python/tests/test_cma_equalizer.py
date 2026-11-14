"""The blind constant-modulus equalizer (conventions: Synchronization, Constant-modulus
equalizer; ADR 0074)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import signalforge as sf

H = np.array([1, 0.35 - 0.2j, -0.1 + 0.05j])


def _rotated_mse(y: np.ndarray, a: np.ndarray) -> float:
    # the blind output keeps the channel's phase: compare after the best single rotation
    turn = np.exp(1j * np.angle(np.sum(a * np.conj(y))))
    return float(np.mean(np.abs(y * turn - a) ** 2))


@pytest.mark.parametrize(
    ("mod", "bits", "modulus", "limit"), [("qpsk", 2, 1.0, 0.012), ("qam16", 4, 1.32, 0.025)]
)
def test_opens_the_eye_with_no_training(mod: str, bits: int, modulus: float, limit: float) -> None:
    # measured in ADR 0074: 0.006 and 0.013 over the last 1000 of 3000
    rng = np.random.default_rng(2)
    mapper = {"qpsk": sf.qpsk_map, "qam16": sf.qam16_map}[mod]
    a = mapper(rng.integers(0, 2, bits * 3000).astype(np.uint8))
    x = np.convolve(a, H)[:3000] * np.exp(0.7j)
    r = sf.cma_equalizer(x, 7, 0.03, modulus=modulus)
    assert _rotated_mse(r.symbols[2000:], a[2000:]) < limit < _rotated_mse(x[2000:], a[2000:])


def test_one_tap_scalar_gain() -> None:
    g = 1.7 * (0.6 - 0.8j)
    x = g * np.exp(1j * np.pi / 4 * np.arange(1, 40, 2))
    r = sf.cma_equalizer(x, 1, 0.5)
    w = 1.0
    for _ in x:
        w *= 1 + 0.5 * (1 - abs(w * g) ** 2)
    assert abs(r.taps[0] - w) < 1e-13
    # the magnitude goes to 1/|g|, the phase stays where it started
    assert abs(abs(r.taps[0]) - 1 / 1.7) < 1e-9


def test_its_taps_start_a_decision_directed_lms() -> None:
    rng = np.random.default_rng(4)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * 3000).astype(np.uint8))
    x = np.convolve(a, H)[:3000] * np.exp(0.3j)
    blind = sf.cma_equalizer(x, 7, 0.03)
    # the blind output's pi/2 ambiguity is resolved here with the known symbols, as a preamble would
    turn = np.exp(
        1j * np.pi / 2 * np.round(np.angle(np.sum(a * np.conj(blind.symbols))) / (np.pi / 2))
    )
    r = sf.lms_equalizer(x, [], 7, 0.05, decision="qpsk", initial_taps=blind.taps * turn)
    trained = sf.lms_equalizer(x, a, 7, 0.05)
    # as good as training on every symbol: 7 taps leave about 0.007 on this channel either way
    mse = [float(np.mean(np.abs(z.symbols[2000:] - a[2000:]) ** 2)) for z in (r, trained)]
    assert mse[0] < 1.1 * mse[1] < 0.01


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"modulus": 0.0}, "modulus"),
        ({"modulus": math.inf}, "modulus"),
        ({"step": 2.5}, "step"),
        ({"initial_taps": [1, 0]}, "initial_taps"),
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        sf.cma_equalizer(**{"samples": [1, 1j, -1], "num_taps": 3, "step": 0.5, **kw})
