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


@pytest.mark.parametrize("complex_out", [True, False])
def test_multitone_is_the_sum_of_tones(complex_out: bool) -> None:
    f, a, p = [10.0, -37.5, 200.0], [1.0, 0.5, 2.0], [0.1, 2.0, -3.0]
    x = waveforms.multitone(1000.0, 57, f, a, p, complex=complex_out)
    expected = sum(
        waveforms.tone(1000.0, 57, fk, ak, pk, complex=complex_out)
        for fk, ak, pk in zip(f, a, p, strict=True)
    )
    assert np.allclose(x, expected, rtol=0, atol=1e-14)
    assert x.dtype == (np.complex128 if complex_out else np.float64)
    ones = waveforms.multitone(1000.0, 8, f, complex=complex_out)
    assert np.allclose(
        ones, waveforms.multitone(1000.0, 8, f, [1, 1, 1], [0, 0, 0], complex=complex_out)
    )


def test_newman_phases_lower_the_crest_factor() -> None:
    k = 32
    f = np.arange(1, k + 1, dtype=np.float64)

    def crest(phases: Any) -> float:
        x = waveforms.multitone(1024.0, 1024, f, phases=phases)
        return float(np.max(np.abs(x)) / np.sqrt(np.mean(np.abs(x) ** 2)))

    assert crest(None) == pytest.approx(np.sqrt(k), rel=1e-12)  # all peak together at n = 0
    assert crest(waveforms.newman_phases(k)) < 0.4 * crest(None)


def test_chirp_instantaneous_frequency_is_linear() -> None:
    fs, n, f0, f1 = 1e4, 500, -1500.0, 2500.0
    x = waveforms.chirp(fs, n, f0, f1)
    inst = np.angle(x[1:] * np.conj(x[:-1])) * fs / (2 * np.pi)
    assert np.allclose(inst, f0 + (f1 - f0) * (np.arange(n - 1) + 0.5) / n, rtol=0, atol=1e-8)
    real = waveforms.chirp(fs, n, f0, f1, 2.0, 0.3, complex=False)
    assert np.allclose(real, (2 * waveforms.chirp(fs, n, f0, f1, 1.0, 0.3)).real, atol=1e-13)


def test_chirps_join_without_a_frequency_jump() -> None:
    fs, n = 1000.0, 200
    first = waveforms.chirp(fs, n, 10.0, 90.0)
    theta_end = 2 * np.pi * (10.0 * n / fs + (90.0 - 10.0) * (n / fs) / 2)
    second = waveforms.chirp(fs, n, 90.0, 10.0, phase=theta_end)
    x = np.concatenate([first, second])
    inst = np.angle(x[1:] * np.conj(x[:-1])) * fs / (2 * np.pi)
    assert np.max(np.abs(np.diff(inst))) < 0.5  # 80 Hz over 200 samples is 0.4 Hz a sample


def test_constant_chirp_is_a_tone() -> None:
    assert np.allclose(
        waveforms.chirp(48e3, 64, 1e3, 1e3, 0.5, 1.0),
        waveforms.tone(48e3, 64, 1e3, 0.5, 1.0),
        atol=1e-14,
    )


@pytest.mark.parametrize("delay", [-13, -1, 0, 3, 1000])
def test_pulse_train_matches_its_definition(delay: int) -> None:
    x = waveforms.pulse_train(100, 7, 3, 1.5, delay)
    n = np.arange(100)
    assert np.array_equal(x, np.where((n - delay) % 7 < 3, 1.5, 0.0))
    assert x.dtype == np.float64


@pytest.mark.parametrize(
    ("call", "args"),
    [
        (waveforms.multitone, (1.0, 4, [])),
        (waveforms.multitone, (1.0, 4, [[0.1]])),
        (waveforms.multitone, (1.0, 4, [0.1j])),
        (waveforms.multitone, (1.0, 4, [np.nan])),
        (waveforms.multitone, (1.0, 4, [0.1], [np.inf])),
        (waveforms.multitone, (1.0, 4, [0.1], None, [0.0, 1.0])),
        (waveforms.multitone, (1.0, 4.0, [0.1])),
        (waveforms.newman_phases, (0,)),
        (waveforms.newman_phases, (2.0,)),
        (waveforms.newman_phases, (True,)),
        (waveforms.chirp, (0.0, 4, 0.0, 1.0)),
        (waveforms.chirp, (1.0, -1, 0.0, 1.0)),
        (waveforms.chirp, (1.0, 4, np.nan, 1.0)),
        (waveforms.chirp, (1.0, 4, 0.0, np.inf)),
        (waveforms.chirp, (1.0, 4, 0.0, 1.0, np.nan)),
        (waveforms.chirp, (1.0, 4, 0.0, 1.0, 1.0, np.inf)),
        (waveforms.pulse_train, (4, 0, 0)),
        (waveforms.pulse_train, (4, 2, 3)),
        (waveforms.pulse_train, (4, 2, -1)),
        (waveforms.pulse_train, (-1, 2, 1)),
        (waveforms.pulse_train, (4, 2, 1, np.nan)),
        (waveforms.pulse_train, (4, 2, 1, 1.0, 0.5)),
        (waveforms.pulse_train, (4, 2, 1, 1.0, True)),
        (waveforms.tone, (1.0, 4, np.nan)),
        (waveforms.tone, (1.0, 4, 0.1, np.inf)),
        (waveforms.tone, (1.0, 4, 0.1, 1.0, np.nan)),
    ],
)
def test_new_generators_reject_bad_arguments(call: Any, args: tuple[Any, ...]) -> None:
    with pytest.raises(ValueError):
        call(*args)
