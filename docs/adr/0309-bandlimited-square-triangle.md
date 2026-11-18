# ADR 0309: Band-limited square and triangle

Status: accepted, 2026-11-17.

## Context

The band-limited sawtooth (ADR 0307) sums its Fourier series up to the Nyquist frequency so
nothing aliases. The square at duty 1/2 and the triangle have series of odd harmonics only, with
amplitudes falling as `1/k` and `1/k²`. They complete the classic set without aliasing. A square
at another duty is the difference of two shifted sawtooths, which the caller can form.

## Decision

- **The API.**
  - Python, in `waveforms`:
    - `bandlimited_square(sample_rate, num_samples, frequency, amplitude=1, phase=0)`;
    - `bandlimited_triangle(sample_rate, num_samples, frequency, amplitude=1, phase=0)`.
  - C#: `Waveforms.BandlimitedSquare` and `Waveforms.BandlimitedTriangle`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u` and `K` are as for the band-limited sawtooth. The sums run over odd `k` from 1 up to
    `K`, in increasing order.
  - Square: `S = Σ sin((2π·k)·u)/k` and `y = ((4·A)/π)·S`. The full series is the naive square
    at duty 1/2: `A` for `u < 1/2`, `−A` after.
  - Triangle: `S = Σ cos((2π·k)·u)/(k·k)` and `y = ((8·A)/(π·π))·S`. The full series is the
    naive triangle, `A` at the start of a cycle.
  - `K = 0` gives silence.
  - The sawtooth's `K` is now computed by a helper the three share, with the same result.
- **The rules.** As for the band-limited sawtooth: `sample_rate` positive and finite,
  `num_samples` at least 0, `frequency` finite and not 0, `amplitude` and `phase` finite.

## Consequences

- **Vectors.**
  - Expected values come from the series with `u` in exact rationals, rounded once, and stdlib
    `math.sin` and `math.cos`.
  - The tolerance is `abs 1e-12, rel 1e-11`.
  - The Python tests check the harmonics against the series and nothing else below Nyquist.
