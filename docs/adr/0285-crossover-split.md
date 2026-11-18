# ADR 0285: Two-band splitter

Status: accepted, 2026-11-17.

## Context

ADR 0284 designs a Linkwitz-Riley crossover as two cascades of sections. To use it a caller
builds two `IirFilter`s and runs the signal through each. A splitter does that in one call and
returns the two signals. It is the first stage of a multiband processor, and the de-esser and
any later multiband dynamics can be built on it.

## Decision

- **The API.**
  - Python: `crossover_split(samples, order, cutoff, sample_rate)` in `dsp`, returning a new
    frozen dataclass `Bands(low, high)` of real arrays.
  - C#: `Dsp.CrossoverSplit(samples, order, cutoff, sampleRate)`, returning
    `sealed record Bands(double[] Low, double[] High)`.
  - Real input only.
- **The value.**
  - `x = linkwitz_riley(order, cutoff, fs)`.
  - `low` is `IirFilter(x.low).process(samples)` and `high` is `IirFilter(x.high).process(samples)`,
    each from rest and each as long as the input.
  - `low + high` is the input passed through the crossover's all-pass.
- **The rules.**
  - The crossover's rules for `order`, `cutoff` and `fs`.
  - The samples must be real, finite and at least one.

## Consequences

- **Vectors.**
  - Expected values come from the stdlib Butterworth sections of ADR 0284's generator, run as
    difference equations in exact rationals at the float coefficients.
  - The tolerance is `abs 1e-12, rel 1e-12`.
