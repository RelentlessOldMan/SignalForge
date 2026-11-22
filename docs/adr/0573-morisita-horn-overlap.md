# ADR 0573: The Morisita–Horn overlap

Status: accepted, 2026-11-22.

## Context

Horn (1966) simplified Morisita's overlap index for shares:
`C = 2 Σ pᵢqᵢ/(Σ pᵢ² + Σ qᵢ²)`, `pᵢ` and `qᵢ` the shares of kind `i` in each record. It
is symmetric, 1 for proportional records and 0 when they share nothing. It differs from
Pianka's overlap only in its denominator, the arithmetic rather than the geometric mean of
the two Simpson concentrations, so it is at most Pianka's overlap.

## Decision

- **The API.**
  - Python: `morisita_horn_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.MorisitaHornOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Each record is divided by its largest value, so totals and squares cannot
  overflow, then by its total, sums in record order. Then
  `2 Σ pᵢqᵢ/(Σ pᵢ² + Σ qᵢ²)`, the sums in record order, capped at 1.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator computes `C` exactly with fractions.
  - The tolerance is `abs 1e-12, rel 1e-12`.
