# ADR 0416: The triangular discrimination

Status: accepted, 2026-11-19.

## Context

The triangular discrimination (Le Cam's divergence) `Σ (Pᵢ − Qᵢ)²/(Pᵢ + Qᵢ)` sits between
the Hellinger distance (ADR 0409) and the total variation distance (ADR 0411): with `H` the
Hellinger distance, `2H² ≤ Δ ≤ 4H²`, and `Δ ≤ 2δ`. Unlike the chi-square divergence
(ADR 0412) it is symmetric and bounded, so it takes distributions with different supports.

## Decision

- **The API.**
  - Python: `triangular_discrimination(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.TriangularDiscrimination(ReadOnlySpan<double> p,
    ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence (ADR 0407): each by its own sum.
- **The value.**
  - `Δ(P, Q) = Σᵢ (Pᵢ − Qᵢ)²/(Pᵢ + Qᵢ)`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Indices where both are zero are dropped. Per index, the
    difference squared as a product, over the sum; the terms are summed in order and clamped
    to at most 2.
  - Symmetric; from 0 (the same) to 2 (no shared support).
- **The rules.**
  - As for the Hellinger distance: equal lengths at least 1, finite, non-negative, each sum
    above zero, zeros anywhere.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-13`.
