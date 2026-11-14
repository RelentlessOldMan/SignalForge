"""RLS training for the decision-feedback equalizer and the link (conventions: Synchronization,
Decision-feedback equalizer; ADR 0077)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

import signalforge as sf
from signalforge.link import QpskLinkConfig

H = np.array([1, 0.9 * np.exp(0.6j)])


def _hard(seed: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * n).astype(np.uint8))
    x = np.convolve(a, H)[:n] + 0.05 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return a, x


def test_forward_only_is_the_rls_equalizer() -> None:
    a, x = _hard(1, 300)
    d = sf.dfe_equalizer(x, a[:50], 9, 0, 0.5, center=2, decision="qpsk", forgetting=0.99)
    r = sf.rls_equalizer(x, a[:50], 9, 0.99, center=2, decision="qpsk")
    assert np.max(np.abs(d.symbols - r.symbols)) < 1e-12
    assert np.max(np.abs(d.taps - r.taps)) < 1e-12


def test_step_is_not_used() -> None:
    a, x = _hard(2, 200)
    kw = {"decision": "qpsk", "phase_loop_gains": (0.02, 0.0), "forgetting": 0.995}
    p = sf.dfe_equalizer(x, a[:40], 7, 2, 0.0, **kw)  # type: ignore[arg-type]
    q = sf.dfe_equalizer(x, a[:40], 7, 2, 1.5, **kw)  # type: ignore[arg-type]
    assert np.array_equal(p.symbols, q.symbols)


def test_taps_are_the_least_squares_solution() -> None:
    # training covers every output, so the feedback regressor is the known symbols
    a, x = _hard(3, 60)
    taps, m, c = 5, 2, 1
    r = sf.dfe_equalizer(x, a, taps, m, 0.5, center=c, forgetting=1.0, delta=0.01)
    z = np.array(
        [
            [x[n + c - i] if 0 <= n + c - i < len(x) else 0 for i in range(taps)]
            + [a[n - j] if n - j >= 0 else 0 for j in range(1, m + 1)]
            for n in range(60)
        ]
    )
    start = np.eye(taps + m)[c]
    w = np.linalg.solve(0.01 * np.eye(taps + m) + z.conj().T @ z, 0.01 * start + z.conj().T @ a)
    assert np.max(np.abs(np.concatenate([r.taps, r.feedback_taps]) - w)) < 1e-9


def _link(mod: str, seed: int, forgetting: float | None) -> QpskLinkConfig:
    return QpskLinkConfig(
        modulation=mod,
        num_symbols=2000,
        preamble_symbols=100,
        eb_n0_db=14.0 if mod == "qam16" else 12.0,
        frequency_offset_hz=5.0,
        multipath_delays=(0, 4),
        multipath_gains=((1.0, 0.0), (0.9, 0.0)),
        equalizer_taps=11,
        equalizer_feedback=2,
        equalizer_loop_gains=(0.02, 0.0001),
        equalizer_forgetting=forgetting,
        seed=seed,
    )


@pytest.mark.parametrize("mod", ["qam16", "psk8"])
def test_link_short_preamble_from_the_impulse(mod: str) -> None:
    # measured in ADR 0077: LMS from the impulse fails on every seed, RLS at most 0.0027
    rls = [sf.qpsk_link(_link(mod, s, 0.999)).bit_errors.rate for s in range(80, 84)]
    lms = [sf.qpsk_link(_link(mod, s, None)).bit_errors.rate for s in range(80, 84)]
    assert max(rls) < 0.005 < 0.2 < min(lms)


def test_link_rejects() -> None:
    c = _link("qpsk", 80, 0.999)
    for bad in (0.0, 1.5, float("nan")):
        with pytest.raises(ValueError, match="equalizer_forgetting"):
            sf.qpsk_link(dataclasses.replace(c, equalizer_forgetting=bad))
    with pytest.raises(ValueError, match="equalizer_forgetting needs equalizer_taps"):
        sf.qpsk_link(
            dataclasses.replace(
                c, equalizer_taps=None, equalizer_feedback=0, equalizer_loop_gains=None
            )
        )
