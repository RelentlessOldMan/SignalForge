# ADR 0334: Katz fractal dimension

Status: accepted, 2026-11-18.

## Context

Katz (1988) gave a fractal dimension for waveforms that needs no fit: it compares the length of
the curve with its extent. It is cheap and appears next to Higuchi's (ADR 0330) and Petrosian's
(ADR 0335) in EEG feature sets. The published variants differ in how they measure the steps,
so this ADR fixes one.

## Decision

- **The API.**
  - Python: `katz_dimension(samples)` in `measurements`, giving a float.
  - C#: `Measurements.KatzDimension(ReadOnlySpan<double> samples)`.
- **The value.** The waveform is the points `(i, x[i])`, with the index in samples and the
  value in sample units, as in Katz's paper.
  - There are `n = N − 1` steps.
  - `L = Σ_{i=0}^{N−2} sqrt(1 + (x[i+1] − x[i])²)` is the length of the curve.
  - `d = max_i sqrt(i² + (x[i] − x[0])²)` is the largest distance from the first point.
  - `D = log10 n / (log10 n + log10(d/L))`.
- **The rules.**
  - `samples` real, one-dimensional, finite and at least 3 long.
  - The denominator must be above 0, which fails when `n·d ≤ L`. An example is `0, 3, 0`.
- **Units.** The result depends on the scale of the values against the index. Scaling the
  samples changes it, and that is how Katz defined it.

## Consequences

- **Vectors.**
  - The generator uses `math.hypot` and `math.fsum`. The square roots are irrational, so the
    values are float.
  - A straight line gives `d = L` and `D = 1`, which the generator asserts.
  - The tolerance is `abs 1e-13, rel 1e-12`.
