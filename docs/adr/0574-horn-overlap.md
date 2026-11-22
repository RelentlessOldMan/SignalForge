# ADR 0574: Horn's information overlap

Status: accepted, 2026-11-22.

## Context

Horn (1966) measured the overlap of two samples by information:
`R₀ = (Σ (xᵢ+yᵢ) ln(xᵢ+yᵢ) − Σ xᵢ ln xᵢ − Σ yᵢ ln yᵢ)/((X+Y) ln(X+Y) − X ln X − Y ln Y)`,
`X` and `Y` the totals, `0 ln 0 = 0`. It is 1 for proportional records and 0 when they share
nothing. It works on the values themselves, not their shares: it is unchanged when both
records are scaled together, but not when one is scaled alone, unless they are
proportional.

## Decision

- **The API.**
  - Python: `horn_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.HornOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Both records are divided by the largest value in either, so totals cannot
  overflow. Each term `(a+b) ln(a+b) − a ln a − b ln b` is written
  `a·log1p(b/a) + b·log1p(a/b)`, 0 when `a` or `b` is 0, so nothing cancels; the
  denominator is the same form on the totals. Sums in record order; the ratio is capped
  at 1.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator evaluates the definition directly in 60-digit decimal from the exact
    values.
  - The tolerance is `abs 1e-12, rel 1e-12`.
