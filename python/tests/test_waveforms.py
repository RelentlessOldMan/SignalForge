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
