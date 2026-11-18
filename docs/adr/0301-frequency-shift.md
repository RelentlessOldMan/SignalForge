# ADR 0301: Frequency shifter

Status: accepted, 2026-11-17.

## Context

A pitch shifter multiplies every frequency by a ratio and keeps harmonics harmonic. A frequency
shifter adds the same number of hertz to every component instead, so harmonics stop being
harmonic and the sound turns bell-like or metallic. It is Bode's shifter: single-sideband
modulation of the analytic signal. The analytic signal exists (ADR 0185). Ring modulation
(ADR 0262) gives both sidebands; this keeps one.

## Decision

- **The API.**
  - Python: `frequency_shift(samples, shift, sample_rate)` in `spectral`, beside
    `analytic_signal`.
  - C#: `Spectral.FrequencyShift(samples, shift, sampleRate)`.
  - Real samples in, real samples out.
- **The value.**
  - `z = analytic_signal(x)`, `θ[n] = (2π·shift)·(n/fs)`.
  - `y[n] = Re(z[n]·e^{jθ[n]}) = Re z[n]·cos θ[n] − Im z[n]·sin θ[n]`, written out that way in
    both languages.
  - A component at `f` with `0 < f < fs/2` moves to `f + shift`. A shift that takes it past
    0 or `fs/2` folds it back: the output is real, so it cannot hold a negative frequency.
  - DC and the Nyquist bin carry no imaginary part in the analytic signal. They come out as
    the input times `cos θ`, which is amplitude modulation, not a shift.
  - The analytic signal is a whole-block FFT, so the shift is exact for a periodic block and
    shows edge effects otherwise, as `analytic_signal` does.
- **The rules.**
  - The samples are as for `analytic_signal`: real, finite, at least one.
  - `shift` finite, of either sign.
  - `fs` finite and positive.

## Consequences

- **Vectors.**
  - Expected values are analytical. A cosine at an exact bin has the analytic signal
    `A·e^{j(ωn + φ)}`, so the output is `A·cos(ωn + φ + θ[n])`. DC and Nyquist inputs give
    `x[n]·cos θ[n]`.
  - The tolerance is `abs 1e-12, rel 0`, for the FFT's rounding.
