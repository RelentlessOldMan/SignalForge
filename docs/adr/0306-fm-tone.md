# ADR 0306: Two-operator FM tone

Status: accepted, 2026-11-17.

## Context

Chowning (1973) showed that one sine modulating the phase of another gives rich, bell- and
brass-like spectra from two oscillators. The spectrum is the carrier plus sidebands at
`fc ± k·fm`, with amplitudes `J_k(I)` set by the modulation index. It is phase modulation of a
tone by a tone; the general modulators in `modulation` handle data, not this synthesis form.

## Decision

- **The API.**
  - Python: `fm_tone(sample_rate, num_samples, carrier, modulator, index, amplitude=1)` in
    `waveforms`.
  - C#: `Waveforms.FmTone(sampleRate, numSamples, carrier, modulator, index, amplitude = 1)`.
  - Real output. `carrier` and `modulator` are in Hz; `index` is the peak phase deviation in
    radians.
- **The value.**
  - `y[n] = A·cos(2π·fc·(n/fs) + I·sin(2π·fm·(n/fs)))`, with `2π·f` formed first and then
    multiplied by `n/fs`, as `tone` does.
  - By the Jacobi–Anger expansion, `y = A·Σ_k J_k(I)·cos(2π(fc + k·fm)·n/fs)`. At `I = 0` it is
    `tone`'s real form.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `carrier`, `modulator`, `index` and `amplitude` finite.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription of the formula.
  - The tolerance is `abs 1e-12, rel 1e-12`: the arguments reach a few hundred radians, and
    `cos` and `sin` libraries may differ by an ulp of those.
  - The Python tests check the sidebands against `J_k(I)` from its power series.
