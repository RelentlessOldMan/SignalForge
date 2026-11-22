# ADR 0543: Gleason's index

Status: accepted, 2026-11-21.

## Context

Gleason (1922) relates the number of kinds to the logarithm of the number of individuals,
`k/ln N`; Margalef's index (ADR 0542) is the same ratio with `k − 1`. As there, the record
holds one count per kind and `k` counts the values above 0.

## Decision

- **The API.**
  - Python: `gleason_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.GleasonIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = k/ln N`, `k` the number of values above 0, `N = Σᵢ xᵢ` added in record order,
    `ln` the natural logarithm.
  - Above 0. It depends on the scale of the values.
- **The rules.**
  - A real, finite, one-dimensional record, every value at least 0, with `N > 1` so the
    logarithm is positive (otherwise `invalid_argument`).

## Consequences

- One pass for the total, one for the count; the Margalef index is `D − 1/ln N`.
- **Vectors.**
  - The generator forms the total exactly and the logarithm in 50-digit `decimal`.
  - The tolerance is `abs 1e-15, rel 1e-14`, for one logarithm and one division.
