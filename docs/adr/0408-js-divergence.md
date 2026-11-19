# ADR 0408: The Jensen–Shannon divergence

Status: accepted, 2026-11-19.

## Context

The Kullback–Leibler divergence (ADR 0407) is not symmetric and is infinite where `q` is zero
under a positive `p`. The Jensen–Shannon divergence compares each distribution with their
average instead. It is symmetric, always finite and bounded by ln 2, and its square root is a
metric.

## Decision

- **The API.**
  - Python: `js_divergence(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.JsDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence: each by its own sum.
- **The value.**
  - `JS = ½·Σᵢ [Pᵢ·ln(Pᵢ/Mᵢ) + Qᵢ·ln(Qᵢ/Mᵢ)]` in nats, `Mᵢ = (Pᵢ + Qᵢ)/2`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, `Mᵢ` is one addition and one division by 2; the
    `P` term (if `Pᵢ > 0`) and then the `Q` term (if `Qᵢ > 0`) are added to the index's sum, each
    one division, the natural logarithm and one product. The index sums are added in order,
    then halved.
  - The result is clamped to `[0, ln 2]` against rounding.
  - Symmetric, up to the order of the two terms at each index.
- **The rules.**
  - As for the Kullback–Leibler divergence, except that zeros may appear anywhere.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distributions exactly in rationals and the logarithms in 40-digit
    decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
