"""Waveform generators: tones, multitones, chirps, oscillators, pulse trains, envelopes
and PRBS. Definitions in
docs/conventions.md."""

from __future__ import annotations

import math
import operator

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count as _count
from ._checks import real

#: ITU-T O.150 PRBS polynomials ``x^m + x^k + 1`` as ``order -> k``.
PRBS_TAPS: dict[int, int] = {7: 6, 9: 5, 11: 9, 15: 14, 20: 3, 23: 18, 31: 28}


def tone(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """``amplitude * exp(j(2*pi*f*n/fs + phase))``, or ``amplitude * cos(...)`` when not complex.

    ``amplitude`` is the peak amplitude and ``phase`` is in radians.
    """
    if not 0 < sample_rate < math.inf:
        raise ValueError("sample_rate must be positive and finite")
    num_samples = _count(num_samples, "num_samples")
    frequency, amplitude = real(frequency, "frequency"), real(amplitude, "amplitude")
    phase = real(phase, "phase")
    arg = 2.0 * np.pi * frequency * (np.arange(num_samples) / sample_rate) + phase
    if complex:
        return np.asarray(amplitude * np.exp(1j * arg), dtype=np.complex128)
    return np.asarray(amplitude * np.cos(arg), dtype=np.float64)


def _finite_vector(v: ArrayLike, what: str) -> NDArray[np.float64]:
    a = np.asarray(v)
    if a.ndim != 1 or np.iscomplexobj(a) or a.dtype == np.bool_:
        raise ValueError(f"{what} must be a 1-D real array")
    a = np.asarray(a, dtype=np.float64)
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{what} must be finite")
    return a


def multitone(
    sample_rate: float,
    num_samples: int,
    frequencies: ArrayLike,
    amplitudes: ArrayLike | None = None,
    phases: ArrayLike | None = None,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """The sum of one :func:`tone` per frequency (conventions: Tones, Multitone)."""
    f = _finite_vector(frequencies, "frequencies")
    if f.size == 0:
        raise ValueError("frequencies needs at least one value")
    a = np.ones(f.size) if amplitudes is None else _finite_vector(amplitudes, "amplitudes")
    p = np.zeros(f.size) if phases is None else _finite_vector(phases, "phases")
    if a.size != f.size or p.size != f.size:
        raise ValueError("amplitudes and phases need one value per frequency")
    out = tone(sample_rate, num_samples, f[0], a[0], p[0], complex=complex)
    for k in range(1, f.size):
        out = out + tone(sample_rate, num_samples, f[k], a[k], p[k], complex=complex)
    return out


def newman_phases(count: int) -> NDArray[np.float64]:
    """Newman's low-crest-factor phases ``pi * k**2 / count`` for ``k = 0 .. count - 1``."""
    n = _count(count, "count")
    if n < 1:
        raise ValueError("count must be at least 1")
    k = np.arange(n, dtype=np.float64)
    return np.asarray(np.pi * k * k / n, dtype=np.float64)


def chirp(
    sample_rate: float,
    num_samples: int,
    start: float,
    stop: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    *,
    complex: bool = True,
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Linear chirp from ``start`` Hz at the first sample to ``stop`` Hz at ``num_samples/fs``
    (conventions: Tones, Linear chirp)."""
    fs = real(sample_rate, "sample_rate")
    if fs <= 0:
        raise ValueError("sample_rate must be positive")
    n = _count(num_samples, "num_samples")
    f0, f1 = real(start, "start"), real(stop, "stop")
    amp, ph = real(amplitude, "amplitude"), real(phase, "phase")
    t = np.arange(n, dtype=np.float64) / fs
    rate = (f1 - f0) / (2 * (n / fs)) if n else 0.0
    arg = 2.0 * np.pi * (f0 * t + rate * (t * t)) + ph
    if complex:
        return np.asarray(amp * np.exp(1j * arg), dtype=np.complex128)
    return np.asarray(amp * np.cos(arg), dtype=np.float64)


def _integer(value: int, what: str) -> int:
    if isinstance(value, bool | np.bool_):
        raise ValueError(f"{what} must be an integer")
    try:
        return operator.index(value)
    except TypeError:
        raise ValueError(f"{what} must be an integer") from None


def pulse_train(
    num_samples: int, period: int, width: int, amplitude: float = 1.0, delay: int = 0
) -> NDArray[np.float64]:
    """Rectangular pulses, in whole samples: ``amplitude`` where ``(n - delay) mod period < width``
    (conventions: Tones, Pulse train)."""
    n = _count(num_samples, "num_samples")
    p = _count(period, "period")
    w = _count(width, "width")
    d = _integer(delay, "delay")
    amp = real(amplitude, "amplitude")
    if p < 1:
        raise ValueError("period must be at least 1")
    if w > p:
        raise ValueError("width must be at most period")
    on = np.mod(np.arange(n, dtype=np.int64) - d, p) < w
    return np.where(on, amp, 0.0).astype(np.float64)


def _cycle(
    sample_rate: float, num_samples: int, frequency: float, amplitude: float, phase: float
) -> tuple[NDArray[np.float64], float]:
    """The phase in cycles, ``u = t - floor(t)``, and the checked amplitude."""
    fs = real(sample_rate, "sample_rate")
    if not fs > 0:
        raise ValueError("sample_rate must be positive and finite")
    size = _count(num_samples, "num_samples")
    f = real(frequency, "frequency")
    amp = real(amplitude, "amplitude")
    p = real(phase, "phase")
    t = f * (np.arange(size) / fs) + p
    return t - np.floor(t), amp


def sawtooth(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive sawtooth ``A(2u - 1)``, ``phase`` in cycles (conventions: Oscillators; ADR 0305)."""
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    y: NDArray[np.float64] = amp * (2 * u - 1)
    return y


def square(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    duty: float = 0.5,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive square, ``A`` for the first ``duty`` of each cycle and ``-A`` after, ``phase`` in
    cycles (conventions: Oscillators; ADR 0305)."""
    d = real(duty, "duty")
    if not 0 <= d <= 1:
        raise ValueError("duty must be in [0, 1]")
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    return np.where(u < d, amp, -amp).astype(np.float64)


def triangle(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive triangle ``A(4|u - 1/2| - 1)``, peaking at the start of each cycle, ``phase`` in
    cycles (conventions: Oscillators; ADR 0305)."""
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    y: NDArray[np.float64] = amp * (4 * np.abs(u - 0.5) - 1)
    return y


def fm_tone(
    sample_rate: float,
    num_samples: int,
    carrier: float,
    modulator: float,
    index: float,
    amplitude: float = 1.0,
) -> NDArray[np.float64]:
    """Two-operator FM, ``A cos(2 pi fc n/fs + I sin(2 pi fm n/fs))`` (conventions: FM tone;
    ADR 0306)."""
    fs = real(sample_rate, "sample_rate")
    if not fs > 0:
        raise ValueError("sample_rate must be positive and finite")
    size = _count(num_samples, "num_samples")
    fc = real(carrier, "carrier")
    fm = real(modulator, "modulator")
    i = real(index, "index")
    amp = real(amplitude, "amplitude")
    t = np.arange(size) / fs
    y: NDArray[np.float64] = amp * np.cos(2.0 * np.pi * fc * t + i * np.sin(2.0 * np.pi * fm * t))
    return y


def bandlimited_sawtooth(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Sawtooth from its Fourier series up to the Nyquist frequency, ``phase`` in cycles
    (conventions: Band-limited sawtooth; ADR 0307)."""
    f = real(frequency, "frequency")
    if f == 0:
        raise ValueError("frequency must not be 0")
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    acc = np.zeros(u.size)
    for k in range(1, _top_harmonic(sample_rate, f) + 1):
        acc += np.sin((2 * np.pi * k) * u) / k
    y: NDArray[np.float64] = ((-2 * amp) / np.pi) * acc
    return y


def _top_harmonic(sample_rate: float, frequency: float) -> int:
    """The largest ``k >= 0`` with ``k |f| < fs/2``, tested in floating point."""
    half = 0.5 * float(sample_rate)
    af = abs(frequency)
    top = int(half / af)
    while (top + 1) * af < half:
        top += 1
    while top > 0 and top * af >= half:
        top -= 1
    return top


def _nonzero_frequency(frequency: float) -> float:
    f = real(frequency, "frequency")
    if f == 0:
        raise ValueError("frequency must not be 0")
    return f


def bandlimited_square(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Square at duty 1/2 from its odd harmonics up to the Nyquist frequency, ``phase`` in
    cycles (conventions: Band-limited square and triangle; ADR 0309)."""
    f = _nonzero_frequency(frequency)
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    acc = np.zeros(u.size)
    for k in range(1, _top_harmonic(sample_rate, f) + 1, 2):
        acc += np.sin((2 * np.pi * k) * u) / k
    y: NDArray[np.float64] = ((4 * amp) / np.pi) * acc
    return y


def bandlimited_triangle(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Triangle from its odd harmonics up to the Nyquist frequency, peaking at the start of
    each cycle, ``phase`` in cycles (conventions: Band-limited square and triangle; ADR 0309)."""
    f = _nonzero_frequency(frequency)
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    acc = np.zeros(u.size)
    for k in range(1, _top_harmonic(sample_rate, f) + 1, 2):
        acc += np.cos((2 * np.pi * k) * u) / (k * k)
    y: NDArray[np.float64] = ((8 * amp) / (np.pi * np.pi)) * acc
    return y


def hard_sync_sawtooth(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    sync_frequency: float,
    amplitude: float = 1.0,
) -> NDArray[np.float64]:
    """Naive sawtooth at ``frequency`` restarted each time a master at ``sync_frequency``
    starts a cycle (conventions: Hard-synced sawtooth; ADR 0315)."""
    m, amp = _cycle(sample_rate, num_samples, sync_frequency, amplitude, 0.0)
    if not real(sync_frequency, "sync_frequency") > 0:
        raise ValueError("sync_frequency must be positive")
    s = (real(frequency, "frequency") / sync_frequency) * m
    y: NDArray[np.float64] = amp * (2 * (s - np.floor(s)) - 1)
    return y


def polyblep_sawtooth(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive sawtooth with the PolyBLEP residual taken off at the jump, ``phase`` in cycles
    (conventions: PolyBLEP sawtooth; ADR 0310)."""
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    f = real(frequency, "frequency")
    if not abs(f) <= 0.5 * sample_rate:
        raise ValueError("|frequency| must be at most sample_rate/2")
    y: NDArray[np.float64] = amp * ((2 * u - 1) - _blep(u, abs(f) / sample_rate))
    return y


def _blep(u: NDArray[np.float64], dt: float) -> NDArray[np.float64]:
    """The PolyBLEP residual at phase ``u`` for a jump at ``u = 0`` (ADR 0310)."""
    r = np.zeros(u.size)
    after = u < dt
    t = u[after] / dt
    r[after] = t + t - t * t - 1
    before = ~after & (u > 1 - dt)
    t = (u[before] - 1) / dt
    r[before] = t * t + t + t + 1
    return r


def polyblep_square(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    duty: float = 0.5,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive square with the PolyBLEP residual at both edges, ``phase`` in cycles
    (conventions: PolyBLEP square; ADR 0311)."""
    d = real(duty, "duty")
    if not 0 <= d <= 1:
        raise ValueError("duty must be in [0, 1]")
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    f = real(frequency, "frequency")
    if not abs(f) <= 0.5 * sample_rate:
        raise ValueError("|frequency| must be at most sample_rate/2")
    return _blep_square(u, d, amp, abs(f) / sample_rate)


def _blep_square(
    u: NDArray[np.float64], d: float | NDArray[np.float64], amp: float, dt: float
) -> NDArray[np.float64]:
    """The square with duty ``d`` and the PolyBLEP residual at both edges (ADR 0311)."""
    low = u < d
    v = u - d
    v[low] += 1
    naive = np.where(low, amp, -amp)
    y: NDArray[np.float64] = naive + amp * _blep(u, dt) - amp * _blep(v, dt)
    return y


def polyblep_pwm(
    duty: ArrayLike,
    sample_rate: float,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Pulse-width modulation with the PolyBLEP residual at both edges, ``phase`` in cycles
    (conventions: PolyBLEP pulse-width modulation; ADR 0313)."""
    d = _finite_vector(duty, "duty")
    if not np.all((d >= 0) & (d <= 1)):
        raise ValueError("duty must be in [0, 1]")
    u, amp = _cycle(sample_rate, d.size, frequency, amplitude, phase)
    f = real(frequency, "frequency")
    if not abs(f) <= 0.5 * sample_rate:
        raise ValueError("|frequency| must be at most sample_rate/2")
    return _blep_square(u, d, amp, abs(f) / sample_rate)


def pwm(
    duty: ArrayLike,
    sample_rate: float,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Square whose duty changes every sample, ``A`` while ``u < duty[n]`` and ``-A`` after,
    ``phase`` in cycles (conventions: Pulse-width modulation; ADR 0312)."""
    d = _finite_vector(duty, "duty")
    if not np.all((d >= 0) & (d <= 1)):
        raise ValueError("duty must be in [0, 1]")
    u, amp = _cycle(sample_rate, d.size, frequency, amplitude, phase)
    return np.where(u < d, amp, -amp).astype(np.float64)


def polyblep_triangle(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """Naive triangle with the PolyBLAMP residual at both corners, ``phase`` in cycles
    (conventions: PolyBLEP triangle; ADR 0314)."""
    u, amp = _cycle(sample_rate, num_samples, frequency, amplitude, phase)
    f = real(frequency, "frequency")
    if not abs(f) <= 0.5 * sample_rate:
        raise ValueError("|frequency| must be at most sample_rate/2")
    dt = abs(f) / sample_rate
    c = np.zeros(u.size)
    d = np.minimum(u, 1 - u)
    near = d < dt
    w = 1 - d[near] / dt
    c[near] -= w * w * w / 6
    d = np.abs(u - 0.5)
    near = d < dt
    w = 1 - d[near] / dt
    c[near] += w * w * w / 6
    y: NDArray[np.float64] = amp * ((4 * np.abs(u - 0.5) - 1) + 8 * dt * c)
    return y


def supersaw(
    sample_rate: float,
    num_samples: int,
    frequency: float,
    detune: float,
    voices: int = 7,
    amplitude: float = 1.0,
) -> NDArray[np.float64]:
    """The mean of ``voices`` PolyBLEP sawtooths spread evenly over ``+-detune`` cents, voice
    ``k`` starting at phase ``k/voices`` (conventions: Supersaw; ADR 0316)."""
    v = _integer(voices, "voices")
    if v < 1:
        raise ValueError("voices must be at least 1")
    c = real(detune, "detune")
    if not c >= 0:
        raise ValueError("detune must be at least 0")
    f = real(frequency, "frequency")
    amp = real(amplitude, "amplitude")
    acc = np.zeros(_count(num_samples, "num_samples"))
    for k in range(v):
        cents = 0.0 if v == 1 else c * (2 * k / (v - 1) - 1)
        acc += polyblep_sawtooth(sample_rate, num_samples, f * 2 ** (cents / 1200), 1.0, k / v)
    y: NDArray[np.float64] = amp * (acc / v)
    return y


def wavetable(
    table: ArrayLike,
    sample_rate: float,
    num_samples: int,
    frequency: float,
    phase: float = 0.0,
) -> NDArray[np.float64]:
    """One cycle of ``table`` played at ``frequency`` with linear interpolation that wraps,
    ``phase`` in cycles (conventions: Wavetable oscillator; ADR 0308)."""
    t = _finite_vector(table, "table")
    if t.size < 1:
        raise ValueError("table must hold at least one entry")
    u, _ = _cycle(sample_rate, num_samples, frequency, 1.0, phase)
    size = t.size
    p = u * size
    i = np.floor(p).astype(np.int64)
    r = p - i
    i[i >= size] -= size
    y: NDArray[np.float64] = t[i] * (1 - r) + t[(i + 1) % size] * r
    return y


def adsr(
    num_samples: int, attack: int, decay: int, sustain: float, release: int, gate: int
) -> NDArray[np.float64]:
    """Attack-decay-sustain-release envelope in whole samples, let go at ``gate``
    (conventions: ADSR envelope; ADR 0303)."""
    size = _count(num_samples, "num_samples")
    if size < 1:
        raise ValueError("num_samples must be at least 1")
    a = _count(attack, "attack")
    d = _count(decay, "decay")
    r = _count(release, "release")
    g = _count(gate, "gate")
    s = real(sustain, "sustain")
    if not 0 <= s <= 1:
        raise ValueError("sustain must be in [0, 1]")

    def held(n: int) -> float:
        if n < a:
            return n / a
        if n < a + d:
            return 1 - (1 - s) * ((n - a) / d)
        return s

    level = held(g)
    out = np.empty(size)
    for n in range(size):
        if n < g:
            out[n] = held(n)
        elif n - g < r:
            out[n] = level * (1 - (n - g) / r)
        else:
            out[n] = 0.0
    return out


def prbs(
    order: int, num_bits: int, *, seed: int | None = None, invert: bool = False
) -> NDArray[np.uint8]:
    """Maximal-length PRBS bits (``uint8``) for the O.150 polynomial of the given order.

    The sequence satisfies ``a[i] = a[i-m] XOR a[i-k]`` for ``x^m + x^k + 1``. ``seed`` gives the
    first ``m`` bits, first bit in the most significant position; the default is all ones.
    """
    order = _count(order, "order")
    num_bits = _count(num_bits, "num_bits")
    if order not in PRBS_TAPS:
        raise ValueError(f"unsupported PRBS order {order}; supported: {sorted(PRBS_TAPS)}")
    m, k = order, PRBS_TAPS[order]
    full = (1 << m) - 1
    state = full if seed is None else _count(seed, "seed")
    if not 0 < state <= full:
        raise ValueError(f"seed must be in 1..{full}")

    period = full
    count = min(num_bits, period)
    out = np.empty(count, dtype=np.uint8)
    # state holds the last m bits, oldest (a[i-m]) in the most significant position.
    for i in range(count):
        bit = (state >> (m - 1)) & 1
        out[i] = bit
        new = bit ^ ((state >> (k - 1)) & 1)  # a[i] = a[i-m] ^ a[i-k], for the bit m ahead
        state = ((state << 1) & full) | new
    if num_bits > period:
        out = np.resize(out, num_bits)
    if invert:
        out ^= 1
    return out
