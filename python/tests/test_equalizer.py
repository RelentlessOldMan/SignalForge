"""LMS equalizer (conventions: Synchronization, LMS equalizer; ADR 0066)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

import signalforge as sf

H = np.array([1.0, 0.35 - 0.2j, -0.1 + 0.05j])


def _qpsk(n: int, seed: int = 0) -> np.ndarray:
    return sf.qpsk_map(np.random.default_rng(seed).integers(0, 2, 2 * n))


def test_learns_a_multipath_channel() -> None:
    a = _qpsk(2000)
    x = np.convolve(a, H)[: a.size]
    r = sf.lms_equalizer(x, a[:300], 11, 0.2, center=2, decision="qpsk")
    assert r.symbols.size == r.errors.size == a.size and r.taps.size == 11
    late = np.abs(r.symbols[-500:] - a[-500:]) ** 2
    assert float(np.mean(late)) < 1e-4  # an 11-tap inverse of a minimum-phase channel
    assert np.array_equal(sf.qpsk_demap_hard(r.symbols[300:]), sf.qpsk_demap_hard(a[300:]))
    # the taps approximate the channel's inverse: equalizer * channel is near a delayed impulse
    combined = np.convolve(r.taps, H)
    assert abs(combined[2] - 1) < 0.01
    assert float(np.max(np.abs(np.delete(combined, 2)))) < 0.01


def test_fractional_spacing_takes_a_half_sample_offset() -> None:
    # two samples per symbol, the symbol energy on the odd samples: a symbol-spaced reader at n*sps
    # would see only zeros; the fractionally spaced taps move the center
    a = _qpsk(1500, 1)
    up = np.zeros(2 * a.size, dtype=np.complex128)
    up[1::2] = a
    x = np.convolve(up, [0.5, 1.0, 0.5])[: up.size]
    r = sf.lms_equalizer(x, a[:400], 8, 0.3, samples_per_symbol=2, decision="qpsk")
    # the last symbol's pulse is cut off by the end of the samples
    assert float(np.mean(np.abs(r.symbols[-300:-1] - a[-300:-1]) ** 2)) < 1e-6


def test_without_decision_the_taps_hold_after_training() -> None:
    a = _qpsk(200, 2)
    x = np.convolve(a, H)[: a.size]
    held = sf.lms_equalizer(x, a[:100], 5, 0.5)
    trained = sf.lms_equalizer(x[:100], a[:100], 5, 0.5)
    assert np.all(held.errors[100:] == 0)
    # the first 100 outputs and the taps after them do not depend on what follows, except through
    # the samples ahead of the center in the last regressors
    assert np.array_equal(held.symbols[:98], trained.symbols[:98])


@pytest.mark.parametrize("decision", ["qpsk", "psk8", "qam16", "qam64"])
def test_decisions_follow_the_demappers(decision: str) -> None:
    mapper = {
        "qpsk": sf.qpsk_map,
        "psk8": sf.psk8_map,
        "qam16": sf.qam16_map,
        "qam64": sf.qam64_map,
    }
    bps = {"qpsk": 2, "psk8": 3, "qam16": 4, "qam64": 6}[decision]
    a = mapper[decision](np.random.default_rng(3).integers(0, 2, bps * 50))
    y = a * (1 + 0.01j)  # near the points, so each decides its own
    r = sf.lms_equalizer(y, [], 1, 0.0, decision=decision)
    np.testing.assert_allclose(r.errors, a - y, atol=1e-15)


def test_input_is_not_changed() -> None:
    x = _qpsk(20)
    t = x[:5].copy()
    before = x.copy()
    sf.lms_equalizer(x, t, 3, 1.0, decision="qpsk")
    assert np.array_equal(x, before) and np.array_equal(t, x[:5])


@pytest.mark.parametrize(
    "kw",
    [
        {"num_taps": True},
        {"num_taps": 2.0},
        {"samples_per_symbol": True},
        {"center": -1},
        {"center": True},
        {"step": float("inf")},
        {"step": True},
        {"decision": 3},
        {"samples": [[1, 2]]},
        {"training": [[1]]},
        {"training": [float("nan")]},
    ],
)
def test_rejects(kw: dict[str, Any]) -> None:
    args: dict[str, Any] = {
        "samples": [1, 1j, -1, -1j],
        "training": [1],
        "num_taps": 3,
        "step": 0.5,
    }
    with pytest.raises(ValueError):
        sf.lms_equalizer(**{**args, **kw})
