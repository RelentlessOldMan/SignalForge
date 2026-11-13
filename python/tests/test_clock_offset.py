"""Sample clock offset against a tone and the timing loop (conventions: Channel, Sample clock
offset)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("ppm", [-1e5, -300.0, 25.0, 2e4, 1e5])
def test_tone_is_read_at_the_new_rate(ppm: float) -> None:
    r = 1 + ppm / 1e6
    x = np.exp(2j * math.pi * 0.05 * np.arange(400))
    y = sf.clock_offset(x, ppm)
    n = np.arange(y.size)
    assert y.size == math.floor(399 / r) + 1
    inner = (n * r > 16) & (n * r < 399 - 16)
    want = np.exp(2j * math.pi * 0.05 * n * r)
    # the default kernel's error floor is about 2e-5 at this frequency
    assert np.abs(y - want)[inner].max() < 5e-5


def test_zero_ppm_returns_the_input() -> None:
    x = np.array([1 + 2j, -0.5j, 3.0, 0.25 - 1j])
    np.testing.assert_array_equal(sf.clock_offset(x, 0.0), x)
    assert sf.clock_offset([], 30.0).size == 0


def test_timing_loop_follows_the_clock() -> None:
    sps, nsym, ppm = 4, 6000, 200.0
    bits = sf.prbs(15, 2 * nsym)
    h = sf.rrc_taps(0.35, sps, 10)
    tx = np.concatenate([sf.pulse_shape(sf.qpsk_map(bits), h, sps), np.zeros(64)])
    first = h.size - 1
    clean = sf.convolve(tx, h)
    late = sf.gardner_timing(clean, sps, 0.0, 0.0, start=first + 0.1).errors[1:1500].mean()
    early = sf.gardner_timing(clean, sps, 0.0, 0.0, start=first - 0.1).errors[1:1500].mean()
    kp, ki = sf.pi_loop_gains(0.01, 1 / math.sqrt(2), float(late - early) / 0.2)
    r = 1 + ppm / 1e6
    y = sf.convolve(sf.clock_offset(tx, ppm), h)
    got = sf.gardner_timing(y, sps, kp, ki, start=round(first / r))
    # symbol k peaks at (first + k*sps)/r: 4.8 samples of drift by the end, over a symbol
    truth = (first + sps * np.arange(got.positions.size)) / r
    err = (got.positions - truth)[500:nsym]
    assert abs(truth[nsym - 1] - (first + sps * (nsym - 1))) > sps
    # the loop sits about 0.017 samples off even without an offset (the detector's bias on this
    # pulse); following the clock adds little to that, and nothing grows along the burst
    still = sf.gardner_timing(clean, sps, kp, ki, start=first)
    bias = (still.positions - (first + sps * np.arange(still.positions.size)))[500:nsym].mean()
    assert abs(err.mean() - bias) < 0.01
    assert abs(err[:2750].mean() - err[2750:].mean()) < 0.01
    assert np.abs(err).max() < 0.15
    errors = sf.bit_errors(bits[1000:], sf.qpsk_demap_hard(got.symbols[500:nsym]))
    assert errors.errors == 0


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.clock_offset([[1.0]], 1.0),
        lambda: sf.clock_offset([1.0], 1.5e5),
        lambda: sf.clock_offset([1.0], math.nan),
        lambda: sf.clock_offset([1.0], 1.0, half_width=0),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
