"""Least-squares equalizer taps and the equalizers' given start (conventions: Synchronization,
Least-squares equalizer taps; ADR 0072)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig, qpsk_link

H = np.array([0.1, 0.9, 0.3 + 0.2j, -0.1 + 0.15j, 0.05, 0.2 - 0.1j])


def _channel(a: np.ndarray, h: np.ndarray, sps: int) -> np.ndarray:
    up = np.zeros(a.size * sps, dtype=np.complex128)
    up[::sps] = a
    return np.convolve(up, h)[: up.size]


def _regressors(x: np.ndarray, t: np.ndarray, taps: int, m: int, sps: int, c: int) -> np.ndarray:
    xp = np.concatenate([np.zeros(taps), x, np.zeros(taps)])
    tp = np.concatenate([np.zeros(m), t])
    rows = [
        np.concatenate([xp[taps + n * sps + c - np.arange(taps)], tp[m + n - np.arange(1, m + 1)]])
        for n in range(t.size)
    ]
    return np.array(rows)


def test_matches_numpy_least_squares() -> None:
    # an independent reference: NumPy's SVD least squares on the same regressors
    rng = np.random.default_rng(3)
    a = sf.qam16_map(rng.integers(0, 2, 4 * 300).astype(np.uint8))
    x = _channel(a, H, 2) + 0.05 * (rng.standard_normal(600) + 1j * rng.standard_normal(600))
    r = sf.dfe_least_squares(x, a[:200], 9, 3, samples_per_symbol=2)
    v = _regressors(x, a[:200], 9, 3, 2, 4)
    ref = np.linalg.lstsq(v, a[:200], rcond=None)[0]
    np.testing.assert_allclose(np.concatenate([r.taps, r.feedback_taps]), ref, atol=1e-10)


def test_noiseless_post_cursor_channel_is_solved_exactly() -> None:
    rng = np.random.default_rng(5)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * 50).astype(np.uint8))
    h = np.array([0.8 - 0.3j, 0.4, -0.2j])
    r = sf.dfe_least_squares(np.convolve(a, h)[: a.size], a, 1, 2)
    np.testing.assert_allclose(r.taps, [1 / h[0]], atol=1e-13)
    np.testing.assert_allclose(r.feedback_taps, -h[1:] / h[0], atol=1e-13)


def test_start_is_already_converged() -> None:
    # from the solved taps the error over the data is near the noise; from an impulse it is not
    rng = np.random.default_rng(7)
    n = 400
    a = sf.qpsk_map(rng.integers(0, 2, 2 * n).astype(np.uint8))
    x = _channel(a, H, 2) + 0.03 * (rng.standard_normal(2 * n) + 1j * rng.standard_normal(2 * n))
    s = sf.dfe_least_squares(x, a[:60], 11, 2, samples_per_symbol=2)
    kw: dict[str, Any] = {"samples_per_symbol": 2, "decision": "qpsk"}
    ls = sf.dfe_equalizer(
        x, a[:60], 11, 2, 0.05, initial_taps=s.taps, initial_feedback=s.feedback_taps, **kw
    )
    imp = sf.dfe_equalizer(x, a[:60], 11, 2, 0.05, **kw)
    mse_ls = float(np.mean(np.abs(ls.symbols[60:] - a[60:]) ** 2))
    mse_imp = float(np.mean(np.abs(imp.symbols[60:] - a[60:]) ** 2))
    assert mse_ls < 0.01 < mse_imp


def test_step_zero_keeps_the_given_start() -> None:
    x = np.exp(1j * np.arange(8.0))
    w0 = np.array([0.3, 1 - 0.2j, 0.1j])
    r = sf.lms_equalizer(x, x[:3], 3, 0.0, initial_taps=w0)
    np.testing.assert_allclose(r.symbols, np.convolve(x, w0)[1:9], atol=1e-15)
    np.testing.assert_array_equal(r.taps, w0)
    b0 = np.array([0.5 + 0.5j])
    d = sf.dfe_equalizer(x, x, 3, 1, 0.0, initial_taps=w0, initial_feedback=b0)
    ref = np.convolve(x, w0)[1:9] + b0[0] * np.concatenate([[0], x[:-1]])
    np.testing.assert_allclose(d.symbols, ref, atol=1e-15)
    np.testing.assert_array_equal(d.feedback_taps, b0)


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"training": np.ones(3)}, "at least num_taps"),
        ({"samples": np.zeros(6), "num_feedback": 0}, "does not determine"),
        ({"num_feedback": -1}, "num_feedback"),
        ({"training": np.ones(7)}, "training"),
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    base: dict[str, Any] = {
        "samples": np.array([1, 1j, -1, -1j, 0.5, 0.25j]),
        "training": np.array([1, -1, 1j, -1j, 1]),
        "num_taps": 3,
        "num_feedback": 1,
    }
    with pytest.raises(ValueError, match=match):
        sf.dfe_least_squares(**{**base, **kw})


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"initial_taps": np.ones(2)}, "initial_taps"),
        ({"initial_taps": np.array([0, math.inf, 0])}, "initial_taps"),
        ({"initial_feedback": np.ones(2)}, "initial_feedback"),
    ],
)
def test_equalizer_rejects_a_bad_start(kw: dict[str, Any], match: str) -> None:
    x = np.ones(4, dtype=np.complex128)
    with pytest.raises(ValueError, match=match):
        sf.dfe_equalizer(x, x, 3, 1, 0.5, **kw)


ECHO = {"multipath_delays": (0, 4), "multipath_gains": ((1.0, 0.0), (0.9, 0.0))}


def _link(**kw: Any) -> QpskLinkConfig:
    base: dict[str, Any] = {
        "modulation": "qam16",
        "num_symbols": 6000,
        "preamble_symbols": 100,
        "eb_n0_db": 14.0,
        "frequency_offset_hz": 5.0,
        "equalizer_taps": 11,
        "equalizer_feedback": 2,
        "equalizer_start": "least_squares",
        "seed": 80,
        **ECHO,
    }
    return QpskLinkConfig(**{**base, **kw})


def test_link_short_preamble_needs_the_least_squares_start() -> None:
    # measured in ADR 0072: 0.0023 against 0.37 from the impulse
    assert qpsk_link(_link()).bit_errors.rate < 0.01
    assert qpsk_link(_link(equalizer_start="impulse")).bit_errors.rate > 0.1


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"equalizer_start": "zeros"}, "equalizer_start must be"),
        (
            {"equalizer_taps": None, "equalizer_feedback": 0, **{k: None for k in ECHO}},
            "equalizer_start needs",
        ),
        ({"preamble_symbols": 12}, "preamble_symbols"),
    ],
)
def test_link_rejects(kw: dict[str, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        qpsk_link(_link(**kw))


def test_report_json_carries_the_start() -> None:
    c = qpsk_link(_link(num_symbols=600, eb_n0_db=None)).to_dict()["config"]
    assert c["equalizer_start"] == "least_squares"
