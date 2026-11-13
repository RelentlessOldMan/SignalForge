from typing import Any

import numpy as np
import pytest

from signalforge import waveforms


def test_tone_power_and_frequency() -> None:
    fs, n, f = 1000.0, 1000, 125.0
    x = waveforms.tone(fs, n, f, amplitude=3.0)
    assert np.mean(np.abs(x) ** 2) == pytest.approx(9.0)
    k = int(np.argmax(np.abs(np.fft.fft(x))))
    assert k * fs / n == pytest.approx(f)


def test_real_tone_is_real_part_of_complex() -> None:
    c = waveforms.tone(48000, 64, 1000, 0.5, 0.3)
    r = waveforms.tone(48000, 64, 1000, 0.5, 0.3, complex=False)
    assert r.dtype == np.float64
    np.testing.assert_allclose(r, c.real, atol=1e-15)


@pytest.mark.parametrize("order", sorted(waveforms.PRBS_TAPS))
def test_prbs_is_maximal_length(order: int) -> None:
    if order > 20:
        pytest.skip("full period too long for a unit test")
    period = 2**order - 1
    bits = waveforms.prbs(order, 2 * period)
    assert int(bits[:period].sum()) == 2 ** (order - 1)
    np.testing.assert_array_equal(bits[:period], bits[period:])
    # No shorter period: the all-ones run of length `order` appears once per period.
    run = np.convolve(bits[:period], np.ones(order, dtype=int), "valid")
    assert int(np.count_nonzero(run == order)) == 1


def test_prbs_long_orders_start_with_seed() -> None:
    for order in (23, 31):
        bits = waveforms.prbs(order, order + 5)
        assert bits[:order].all()


def test_prbs_invert_and_seed() -> None:
    a = waveforms.prbs(9, 100)
    np.testing.assert_array_equal(waveforms.prbs(9, 100, invert=True), 1 - a)
    with pytest.raises(ValueError):
        waveforms.prbs(9, 10, seed=1 << 9)
    assert waveforms.prbs(7, 0).size == 0


@pytest.mark.parametrize("bad", [2.5, 3.0, "3", -1])
def test_counts_must_be_non_negative_integers(bad: Any) -> None:
    with pytest.raises(ValueError):
        waveforms.tone(8, bad, 1)
    with pytest.raises(ValueError):
        waveforms.prbs(7, 10, seed=bad)
    with pytest.raises(ValueError):
        waveforms.prbs(7, bad)


def test_numpy_integers_are_accepted_as_counts() -> None:
    bits = waveforms.prbs(np.int64(7), np.int32(5))  # type: ignore[arg-type]
    assert bits.tolist() == [1, 1, 1, 1, 1]
