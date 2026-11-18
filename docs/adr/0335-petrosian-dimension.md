# ADR 0335: Petrosian fractal dimension

Status: accepted, 2026-11-18.

## Context

Petrosian (1995) estimates a fractal dimension from just the number of sign changes of the
first difference, which is the number of local extrema. It is the cheapest of the common
fractal features and a companion to Katz (ADR 0334) and Higuchi (ADR 0330).

## Decision

- **The API.**
  - Python: `petrosian_dimension(samples)` in `measurements`, giving a float.
  - C#: `Measurements.PetrosianDimension(ReadOnlySpan<double> samples)`.
- **The value.** With `n = N` samples and the first difference `Δ[i] = x[i+1] − x[i]`:
  - `N_Δ` is the number of `i` with `sign(Δ[i])·sign(Δ[i+1]) < 0`. A zero step changes no
    sign, and only the signs are multiplied, so tiny values cannot underflow to a missed
    change.
  - `D = log10 n / (log10 n + log10(n / (n + 0.4·N_Δ)))`.
- **The rules.**
  - `samples` real, one-dimensional, finite and at least 3 long.
  - The value is always defined. `N_Δ ≤ n − 2` keeps the denominator above 0 for `n ≥ 3`.

## Consequences

- **Vectors.**
  - `N_Δ` is an exact integer and the generator takes the logarithms in float.
  - A monotonic series gives exactly 1.
  - The tolerance is `abs 1e-14, rel 1e-13`.
