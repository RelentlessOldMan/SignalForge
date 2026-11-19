# ADR 0409: The Hellinger distance

Status: accepted, 2026-11-19.

## Context

The Jensen–Shannon divergence (ADR 0408) is bounded and symmetric but needs logarithms. The
Hellinger distance compares the square roots of the two distributions, which makes it a true
metric from 0 to 1, defined with zeros anywhere, and cheap.

## Decision

- **The API.**
  - Python: `hellinger_distance(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.HellingerDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence (ADR 0407): each by its own sum.
- **The value.**
  - `H = √(½·Σᵢ(√Pᵢ − √Qᵢ)²)`, the `½` making the largest value 1.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, the difference of the two roots is squared; the
    squares are summed in order, halved and rooted. The result is clamped to at most 1.
  - This form is used rather than `√(1 − Σ√(PᵢQᵢ))`, which loses all precision when the
    distributions are close.
  - Symmetric.
- **The rules.**
  - As for the Jensen–Shannon divergence: equal lengths at least 1, finite, non-negative, each
    sum above zero, zeros anywhere.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distributions exactly in rationals and the roots in 40-digit
    decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
