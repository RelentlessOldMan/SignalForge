# ADR 0571: Pianka's niche overlap

Status: accepted, 2026-11-22.

## Context

Pianka (1973) measures how much two species use the same resources by
`O = Σ pᵢqᵢ / √(Σ pᵢ² Σ qᵢ²)`, `pᵢ` and `qᵢ` the shares of resource `i` in each species'
use. It is symmetric, 1 for proportional records and 0 when they share no resource. The
shares cancel, so it is the cosine of the angle between the two records.

## Decision

- **The API.**
  - Python: `pianka_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PiankaOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - The record names follow `bray_curtis`, so the status entry's `a, b` became `x, y`.
- **The form.** Each record is divided by its largest value, so squares cannot overflow;
  then `Σ xᵢyᵢ/√(Σ xᵢ² · Σ yᵢ²)`, the sums in record order, capped at 1.
- **The rules.** Each record one-dimensional, real, finite, at least 0, not empty, with a
  value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator computes `O²` exactly with fractions and takes its square root in
    60-digit decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
