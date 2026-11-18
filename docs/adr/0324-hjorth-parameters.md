# ADR 0324: Hjorth parameters

Status: accepted, 2026-11-18.

## Context

Hjorth's three numbers describe a signal's power and spectral shape from the time domain
alone. Activity is the variance. Mobility is the RMS frequency in radians per sample.
Complexity is how far the shape is from a pure sine, where it is 1. They are cheap, need no
FFT or window, and are a standard feature for EEG and vibration.

## Decision

- **The API.**
  - Python: `hjorth_parameters(samples)` in `measurements`, giving
    `HjorthParameters(activity, mobility, complexity)`.
  - C#: `Measurements.HjorthParameters(ReadOnlySpan<double> samples)`, giving the record
    `HjorthParameters(Activity, Mobility, Complexity)`.
- **The value.**
  - `var(v)` is the population variance, the mean removed and divided by the length.
  - `d[n] = x[n+1] − x[n]`, of length `N − 1`. `dd[n] = d[n+1] − d[n]`, of length `N − 2`.
  - `activity = var(x)`.
  - `mobility = sqrt(var(d) / var(x))`.
  - `complexity = sqrt(var(dd) / var(d)) / mobility`.
  - The differences are not divided by the sample interval, so mobility is per sample.
- **The rules.**
  - `samples` real, one-dimensional, finite, at least 3 long.
  - `var(x) > 0` and `var(d) > 0`. A constant or a straight ramp has no complexity, so it is
    rejected.

## Consequences

- **Vectors.**
  - The generator takes the samples as exact rationals and computes the three variances
    exactly. It takes the square roots once, in float.
  - The tolerance is `abs 1e-12, rel 1e-12`.
