# ADR 0556: Hutcheson's variance

Status: accepted, 2026-11-21.

## Context

Hutcheson (1970) gives the variance of the plug-in Shannon entropy of `N` counts, to the
first order in `1/N` and the second-order term after it:
`V = (Σ pᵢ ln² pᵢ − (Σ pᵢ ln pᵢ)²)/N + (k − 1)/(2N²)`. It is the variance used in
Hutcheson's t-test between two samples.

## Decision

- **The API.**
  - Python: `hutcheson_variance(samples)` in `measurements`, giving a float in nats².
  - C#: `Measurements.HutchesonVariance(ReadOnlySpan<double> samples)`.
- **The value.**
  - `pᵢ = xᵢ/N`, `N = Σᵢ xᵢ` in record order. For each value above 0, in record order,
    `lᵢ = ln pᵢ`; `L = Σ pᵢ lᵢ` and `Q = Σ pᵢ lᵢ lᵢ` (each product left to right), and `k`
    counts those values.
  - `V = (Q − L·L)/N + (k − 1)/(2·N·N)`.
  - 0 when one value holds the total; `Q − L²` is a variance of `ln pᵢ` and so at least 0
    in exact arithmetic, though rounding may leave it a few units in the last place below.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.

## Consequences

- One pass for the checks, one for the sums.
- **Vectors.**
  - The generator forms the sums in 50-digit decimal.
  - The tolerance is `abs 1e-14, rel 1e-12`: `Q − L²` cancels when the shares are even.
