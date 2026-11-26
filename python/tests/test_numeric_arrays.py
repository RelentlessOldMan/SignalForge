"""The array arguments outside the ADR 0621 sweep refuse non-numbers too (ADR 0622)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge._checks import sample_values

_K = np.arange(64)
_S = list(np.sin(0.3 * _K) + 0.5 * np.cos(0.11 * _K))
_D = list(np.exp(-_K / 4.0))
_DB = list(-1.0 * _K)
_P = [1.0, 2.0, 3.0, 4.0]
_W = [[1.0, 0.5, 0.0, 0.0], [0.0, 0.5, 1.0, 0.5]]
_F = [[1.0, 2.0, 3.0], [2.0, 1.0, 0.5], [0.0, 1.0, 4.0]]
_T = [2.0, 1.8, 1.6, 1.5, 1.3, 1.1]

# (call, good value): the call takes the one array under test.
REAL: dict[str, tuple[Callable[[Any], object], object]] = {
    "gcc_phat.x": (lambda v: sf.gcc_phat(v, _S, 8.0), _S),
    "gcc_phat.y": (lambda v: sf.gcc_phat(_S, v, 8.0), _S),
    "energy_separation": (lambda v: sf.energy_separation(v, 8.0), _S),
    "decay_time": (lambda v: sf.decay_time(v, 100.0), _DB),
    "iacc.left": (lambda v: sf.iacc(v, _S, 1000.0), _S),
    "iacc.right": (lambda v: sf.iacc(_S, v, 1000.0), _S),
    "lateral_fraction.omni": (lambda v: sf.lateral_fraction(v, _S, 1000.0), _S),
    "lateral_fraction.figure_eight": (lambda v: sf.lateral_fraction(_S, v, 1000.0), _S),
    "modulation_transfer.frequencies": (
        lambda v: sf.modulation_transfer(_D, 100.0, v),
        [1.0, 2.0],
    ),
    "psd_confidence_interval": (lambda v: sf.psd_confidence_interval(v, 4.0), _P),
    "coherence_confidence_interval": (
        lambda v: sf.coherence_confidence_interval(v, 4),
        [0.1, 0.5, 0.9],
    ),
    "mfcc.power_spectrum": (lambda v: sf.mfcc(v, _W, 2), _P),
    "mfcc.filterbank": (lambda v: sf.mfcc(_P, v, 2), _W),
    "delta": (lambda v: sf.delta(v), _F),
    "analytic_signal": (lambda v: sf.analytic_signal(v), _S),
    "bass_ratio": (lambda v: sf.bass_ratio(v), _T),
    "treble_ratio": (lambda v: sf.treble_ratio(v), _T),
}
# Arrays that may also be complex.
COMPLEX: dict[str, tuple[Callable[[Any], object], object]] = {
    "Signal": (lambda v: sf.Signal(v, 1.0), _S),
    "iq_imbalance": (lambda v: sf.iq_imbalance(v, 1.0, 0.1), _S),
}


def _bad(good: object, complex_ok: bool) -> dict[str, object]:
    g = np.asarray(good, dtype=np.float64)
    huge = g.astype(object)
    huge.flat[0] = 10**400
    obool = g.astype(object)
    obool.flat[0] = True
    ostr = g.astype(object)
    ostr.flat[0] = "1"
    out: dict[str, object] = {
        "strings": g.astype(str),
        "bytes": g.astype("S"),
        "bools": np.ones(g.shape, dtype=bool),
        "datetime": g.astype(np.int64).astype("datetime64[s]"),
        "timedelta": g.astype(np.int64).astype("timedelta64[s]"),
        "huge_int": huge,
        "object_bool": obool,
        "object_string": ostr,
    }
    if not complex_ok:
        ocx = g.astype(object)
        ocx.flat[0] = 1j
        out["object_complex"] = ocx
    return out


CASES = [(k, b) for k in sorted(REAL) for b in sorted(_bad(REAL[k][1], False))] + [
    (k, b) for k in sorted(COMPLEX) for b in sorted(_bad(COMPLEX[k][1], True))
]


@pytest.mark.parametrize(("name", "bad"), CASES)
def test_rejects_non_numbers(name: str, bad: str) -> None:
    call, good = REAL.get(name) or COMPLEX[name]
    with pytest.raises(ValueError, match="numbers"):
        call(_bad(good, name in COMPLEX)[bad])


@pytest.mark.parametrize("name", sorted(REAL) + sorted(COMPLEX))
def test_accepts_numbers(name: str) -> None:
    call, good = REAL.get(name) or COMPLEX[name]
    g = np.asarray(good, dtype=np.float64)
    for v in (good, g.astype(np.float32), g.astype(object)):
        call(v)


def test_signal_keeps_its_dtype() -> None:
    assert sf.Signal(np.ones(3, np.float32), 1.0).samples.dtype == np.float32
    assert sf.Signal(np.ones(3, np.complex64), 1.0).samples.dtype == np.complex64
    assert sf.Signal(np.array([1, 2]), 1.0).samples.dtype == np.float64


def test_sample_values() -> None:
    a = sample_values(np.array([1, 2.5j, 2**70], dtype=object), "x")
    assert a.dtype == np.complex128
    assert a.tolist() == [1, 2.5j, float(2**70)]
    b = sample_values(np.array([1, 2.5], dtype=object), "x")
    assert b.dtype == np.float64 and b.tolist() == [1.0, 2.5]
    c = np.ones(2, np.complex64)
    assert sample_values(c, "x") is c
    assert sample_values(np.array([1, 2]), "x").dtype == np.float64
