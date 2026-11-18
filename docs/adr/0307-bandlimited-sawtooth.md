# ADR 0307: Band-limited sawtooth

Status: accepted, 2026-11-17.

## Context

The naive sawtooth (ADR 0305) jumps once a cycle, and the jump holds harmonics far above the
Nyquist frequency. Sampled, they fold back as inharmonic tones that are loud at high pitches.
The band-limited sawtooth sums the sawtooth's Fourier series only up to the Nyquist frequency,
so it has nothing to fold. It is exact, but costs one sine per harmonic per sample; BLEP
methods are cheaper approximations and are not this item.

## Decision

- **The API.**
  - Python: `bandlimited_sawtooth(sample_rate, num_samples, frequency, amplitude=1, phase=0)`
    in `waveforms`.
  - C#: `Waveforms.BandlimitedSawtooth`, same arguments.
  - Real output, `phase` in cycles, as for the naive oscillators.
- **The value.**
  - `u` is the oscillators' phase: `t = f·(n/fs) + phase`, `u = t − floor(t)`.
  - `K` is the largest `k ≥ 0` with `k·|f| < fs/2`, tested in floating point as written.
  - `S = Σ_{k=1..K} sin((2π·k)·u)/k`, summed from `k = 1` upwards, and
    `y = ((−2·A)/π)·S`.
  - The full series is the naive `A·(2u − 1)` away from the jump. `K = 0`, when
    `|f| ≥ fs/2`, gives silence.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency` finite and not 0; `amplitude` and `phase` finite.

## Consequences

- **Vectors.**
  - Expected values come from the series with `u` in exact rationals, rounded once, and
    stdlib `math.sin`.
  - The tolerance is `abs 1e-12, rel 1e-11`, for an ulp or two per term over up to a few dozen
    terms.
  - The Python tests check the harmonics against `2A/(πk)` up to the Nyquist frequency and
    nothing above.
