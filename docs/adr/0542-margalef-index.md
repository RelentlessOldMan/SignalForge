# ADR 0542: Margalef's index

Status: accepted, 2026-11-21.

## Context

Margalef (1958) gives species richness relative to sample size as `(k − 1)/ln N`: one
less than the number of kinds present over the natural logarithm of the number of
individuals. As for Menhinick's index (ADR 0541), the record holds one count per kind and
`k` counts the values above 0.

## Decision

- **The API.**
  - Python: `margalef_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.MargalefIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = (k − 1)/ln N`, `k` the number of values above 0, `N = Σᵢ xᵢ` added in record
    order, `ln` the natural logarithm.
  - At least 0, and 0 when one value holds the total. It depends on the scale of the
    values.
- **The rules.**
  - A real, finite, one-dimensional record, every value at least 0, with `N > 1` so the
    logarithm is positive (otherwise `invalid_argument`).

## Consequences

- One pass for the total, one for the count.
- **Vectors.**
  - The generator forms the total exactly and the logarithm in 50-digit `decimal`.
  - The tolerance is `abs 1e-15, rel 1e-14`, for one logarithm and one division; near
    `N = 1` the logarithm is small but exact to its own rounding.
