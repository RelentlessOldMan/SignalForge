# ADR 0544: Good's coverage

Status: accepted, 2026-11-21.

## Context

Good (1953) estimates the share of a population represented by the kinds seen in a
sample as `C = 1 − F₁/N`: one less the number of singletons over the number of
individuals. The record holds one count per kind; a singleton is a value equal to 1.

## Decision

- **The API.**
  - Python: `goods_coverage(samples)` in `measurements`, giving a float.
  - C#: `Measurements.GoodsCoverage(ReadOnlySpan<double> samples)`.
- **The value.**
  - `C = 1 − F₁/N`, `F₁` the number of values exactly equal to 1, `N = Σᵢ xᵢ` added in
    record order.
  - From 0 (every value is 1) to 1 (no value is 1) for whole-number counts, as `F₁ ≤ N`.
    Other values are accepted as they are; with `N < F₁` the value is below 0.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for the count.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`, for one division and one subtraction.
