# ADR 0189: Energy separation (DESA-2)

Status: accepted, 2026-11-16. It builds on the Teager-Kaiser energy of ADR 0188.

## Context

Maragos, Kaiser and Quatieri (1993) separate a signal's Teager energy into an instantaneous
amplitude and frequency. DESA-2 uses the symmetric difference `y[n] = x[n+1] − x[n−1]`, and is
exact for `A·cos(Ωn + φ)`:

- `ψ[x] = A²·sin²Ω`;
- `ψ[y] = 4A²·sin⁴Ω`;

so

- `Ω = ½·arccos(1 − ψ[y]/(2ψ[x]))`;
- `|a| = 2ψ[x]/√ψ[y]`.

It needs only five samples per estimate and no transform. It has three weak points:

- Where an energy is not positive, the formulas break down.
- The arccos argument can leave `[−1, 1]` on real data.
- `Ω` is limited to `[0, π/2]`, that is up to `fs/4`.

## Decision

- **The API.** In `measurements`:
  - Python: `energy_separation(samples, sample_rate)`, returning
    `EnergySeparation(amplitude, frequency)`.
  - C#: `Measurements.EnergySeparation(samples, sampleRate)`, returning the record
    `EnergySeparation(Amplitude, Frequency)`.
  - Both fields are arrays of `N − 4` values for `n = 2 … N−3`, at index `n − 2`.
  - The frequency is in Hz: `Ω·fs/(2π)`, in `[0, fs/4]`.
- **The definition.**
  - `ψ[x]` at `n` is `x[n]² − x[n−1]·x[n+1]`.
  - `ψ[y]` at `n` is `y[n]² − y[n−1]·y[n+1]`.
  - Where both are positive:
    - `c = 1 − ψ[y]/(2ψ[x])`, clamped to `[−1, 1]`;
    - the frequency is `½·arccos(c)·fs/(2π)`;
    - the amplitude is `2ψ[x]/√ψ[y]`.
  - Anywhere else, both values are NaN. NaN marks a point with no estimate; it is not an
    error.
- **The rules.**
  - The input is real, one-dimensional and finite, with at least five samples.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** They come from the cosine identity and from five-sample hand sums:
  - Cosines at two frequencies below `fs/4` give exactly `A` and `Ω·fs/(2π)`.
  - A unit impulse gives `ψ[x] = 1` and `ψ[y] = 1`, so `c = ½`, `fs/12` and amplitude 2.
  - `cos(π(n−2)/2)` reaches `c = −1` exactly: `fs/4` and amplitude 1.
  - A case whose `c` falls below −1 is clamped: `fs/4` and amplitude `2/3`.
  - A constant has no positive energy, so it gives NaN.
  - A Fibonacci run gives one estimate (`fs/12`, amplitude 2) and then a NaN, where `ψ[x] = −1`.
