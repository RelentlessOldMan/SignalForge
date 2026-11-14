"""The decision-feedback equalizer (conventions: Synchronization, Decision-feedback equalizer;
ADR 0069)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

H1 = 0.95  # the channel 1 + 0.95 z^-1 has a notch 26 dB deep at half the symbol rate
N0 = 0.01


def _deep_null(seed: int, n: int = 20000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    a = sf.qpsk_map(rng.integers(0, 2, 2 * n).astype(np.uint8))
    noise = math.sqrt(N0 / 2) * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return a, a + H1 * np.concatenate([[0], a[:-1]]) + noise


def _bounds() -> tuple[float, float]:
    """The MMSE linear and decision-feedback equalizers' MSE for 1 + h z^-1 at N0, from the
    folded spectrum S = A' + B cos w: with A = 1 + h^2 + N0 and B = 2h, (1/2pi) int N0/(S + N0) =
    N0/sqrt(A^2 - B^2) and N0 exp(-(1/2pi) int ln(S + N0)) = 2 N0/(A + sqrt(A^2 - B^2))."""
    a, b = 1 + H1 * H1 + N0, 2 * H1
    r = math.sqrt(a * a - b * b)
    return N0 / r, 2 * N0 / (a + r)


def test_no_feedback_is_the_lms_equalizer_exactly() -> None:
    a, x = _deep_null(3, 500)
    lms = sf.lms_equalizer(x, a[:100], 7, 0.3, center=2, decision="qpsk")
    dfe = sf.dfe_equalizer(x, a[:100], 7, 0, 0.3, center=2, decision="qpsk")
    assert np.array_equal(dfe.symbols, lms.symbols)
    assert np.array_equal(dfe.errors, lms.errors)
    assert np.array_equal(dfe.taps, lms.taps)
    assert dfe.feedback_taps.shape == (0,)


def test_feedback_beats_any_linear_equalizer_on_a_deep_null() -> None:
    a, x = _deep_null(1)
    le, dfe_bound = _bounds()
    lms = sf.lms_equalizer(x, a[:2000], 21, 0.02, center=0, decision="qpsk")
    dfe = sf.dfe_equalizer(x, a[:2000], 3, 2, 0.02, center=0, decision="qpsk")
    mse_lms = float(np.mean(np.abs(lms.symbols[10000:] - a[10000:]) ** 2))
    mse_dfe = float(np.mean(np.abs(dfe.symbols[10000:] - a[10000:]) ** 2))
    assert mse_lms > 0.95 * le  # no linear filter does better than the MMSE one
    # the MMSE-DFE bound, with a test allowance for misadjustment and a finite forward filter
    assert 0.95 * dfe_bound < mse_dfe < 1.3 * dfe_bound


def test_a_posteriori_error_is_zero_at_step_one() -> None:
    # with step 1 the updated taps give the reference exactly on the regressor they were updated
    # on: the last output's forward samples and the references before it
    a, x = _deep_null(5, 50)
    for k in (1, 2, 5, 30):
        r = sf.dfe_equalizer(x[:k], a[:k], 4, 3, 1.0, center=1)
        u = [x[k - 1 + 1 - i] if 0 <= k - i < k else 0 for i in range(4)]
        past = [a[k - 1 - j] if k - 1 - j >= 0 else 0 for j in range(1, 4)]
        y = sum(w * ui for w, ui in zip(r.taps, u, strict=True))
        y += sum(b * pj for b, pj in zip(r.feedback_taps, past, strict=True))
        assert y == pytest.approx(a[k - 1], abs=1e-12)


@pytest.mark.parametrize(
    ("kw", "match"),
    [
        ({"num_feedback": -1}, "num_feedback"),
        ({"decision": None}, "num_feedback"),
        ({"step": 2.5}, "step"),
        ({"num_taps": 0}, "num_taps"),
    ],
)
def test_rejects(kw: dict[str, object], match: str) -> None:
    args: dict[str, object] = {
        "samples": [1, 1j, -1, -1j],
        "training": [1],
        "num_taps": 3,
        "num_feedback": 2,
        "step": 0.5,
        "decision": "qpsk",
    }
    args |= kw
    with pytest.raises(ValueError, match=match):
        sf.dfe_equalizer(**args)  # type: ignore[arg-type]
