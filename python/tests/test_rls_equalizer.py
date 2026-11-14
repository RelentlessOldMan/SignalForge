"""The recursive-least-squares equalizer (conventions: Synchronization, RLS equalizer; ADR
0076)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import signalforge as sf

# a zero at radius 0.9: badly conditioned, so normalized LMS converges slowly (ADR 0076)
H = np.array([1, 0.9 * np.exp(0.6j)])


def _hard(seed: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * n).astype(np.uint8))
    x = np.convolve(a, H)[:n] + 0.05 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return a, x


def test_converges_where_lms_is_slow() -> None:
    # measured in ADR 0076 over 20 seeds: RLS 0.06 over symbols 25-49, LMS (step 0.5) 0.32;
    # after 400 symbols RLS about 0.03, LMS still 0.11
    early, late = [], []
    for seed in range(10):
        a, x = _hard(seed, 400)
        r = sf.rls_equalizer(x, a, 15, 1.0, center=2).symbols
        m = sf.lms_equalizer(x, a, 15, 0.5, center=2).symbols
        early.append([np.mean(np.abs(z[25:50] - a[25:50]) ** 2) for z in (r, m)])
        late.append([np.mean(np.abs(z[300:] - a[300:]) ** 2) for z in (r, m)])
    e, lt = np.mean(early, axis=0), np.mean(late, axis=0)
    assert e[0] < 0.1 < 0.2 < e[1]
    assert lt[0] < 0.05 < 0.08 < lt[1]


@pytest.mark.parametrize(("lam", "delta"), [(1.0, 0.01), (0.95, 0.3)])
def test_taps_are_the_weighted_least_squares_solution(lam: float, delta: float) -> None:
    a, x = _hard(3, 60)
    taps, c = 6, 1
    r = sf.rls_equalizer(x, a, taps, lam, delta=delta, center=c)
    # the regressors as the conventions define them, solved directly
    u = np.array(
        [[x[n + c - i] if 0 <= n + c - i < len(x) else 0 for i in range(taps)] for n in range(60)]
    )
    wts = lam ** np.arange(59, -1, -1)
    w0 = np.eye(taps)[c]
    big = lam**60 * delta * np.eye(taps) + (u.conj().T * wts) @ u
    rhs = lam**60 * delta * w0 + (u.conj().T * wts) @ a
    assert np.max(np.abs(r.taps - np.linalg.solve(big, rhs))) < 1e-9


def test_one_tap_gain_closed_form() -> None:
    a = sf.qpsk_map(np.array([0, 1, 1, 0, 1, 1, 0, 0], dtype=np.uint8))
    r = sf.rls_equalizer(2 * a, a, 1, 1.0, delta=0.5)
    n = np.arange(4)
    assert np.allclose(r.symbols, 2 * a * (0.5 + 2 * n) / (0.5 + 4 * n), atol=1e-14)


def test_decisions_carry_on_after_a_short_training() -> None:
    a, x = _hard(5, 600)
    r = sf.rls_equalizer(x, a[:40], 15, 0.995, center=2, decision="qpsk")
    assert np.mean(np.abs(r.symbols[300:] - a[300:]) ** 2) < 0.05
    held = sf.rls_equalizer(x, a[:40], 15, 0.995, center=2)
    assert np.all(held.errors[40:] == 0)  # no decision: the taps hold after the training
    assert np.allclose(held.taps, sf.rls_equalizer(x[:80], a[:40], 15, 0.995, center=2).taps)


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"forgetting": 0.0}, "forgetting"),
        ({"forgetting": 1.5}, "forgetting"),
        ({"forgetting": math.nan}, "forgetting"),
        ({"delta": 0.0}, "delta"),
        ({"delta": math.inf}, "delta"),
        ({"decision": "bpsk"}, "decision"),
        ({"initial_taps": [1, 0]}, "initial_taps"),
    ],
)
def test_rejects(kw: dict[str, Any], match: str) -> None:
    base: dict[str, Any] = {
        "samples": [1, 1j, -1, -1j],
        "training": [1],
        "num_taps": 3,
        "forgetting": 0.99,
    }
    with pytest.raises(ValueError, match=match):
        sf.rls_equalizer(**{**base, **kw})
