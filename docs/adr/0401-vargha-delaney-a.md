# ADR 0401: The Vargha–Delaney A

Status: accepted, 2026-11-19.

## Context

Vargha and Delaney (2000) recommended the probability of superiority as an effect size: the
chance that a value drawn from one sample exceeds one drawn from the other, ties counting
half. It is `(δ + 1)/2` for Cliff's delta δ (ADR 0400) and the Mann–Whitney U over
`n_x·n_y`; it reads as a probability, which δ does not.

## Decision

- **The API.**
  - Python: `vargha_delaney_a(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.VarghaDelaneyA(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - Above 1/2 when `x` tends to be larger.
- **The value.**
  - `A = (2·#(xᵢ > yⱼ) + #(xᵢ = yⱼ))/(2·n_x·n_y)` over all pairs, from 0 to 1.
  - The counts are whole numbers, found by sorting `y` and searching it as Cliff's delta does;
    the numerator and the denominator are converted to `double`, then one division. It is not
    formed from δ, which would round twice.
  - `A(y, x) = 1 − A(x, y)`.
- **The rules.**
  - As for Cliff's delta: each sample one-dimensional, real, finite, at least 1.

## Consequences

- The cost is that of Cliff's delta.
- **Vectors.**
  - The generator compares every pair.
  - The tolerance is `abs 1e-15, rel 1e-15`.
