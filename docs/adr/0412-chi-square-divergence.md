# ADR 0412: The Pearson chi-square divergence

Status: accepted, 2026-11-19.

## Context

The Pearson chi-square divergence of `P` from `Q` is the expected squared relative error
`(P/Q − 1)²` under `Q`: the population form of the chi-square goodness-of-fit statistic. It
bounds the Kullback–Leibler divergence (ADR 0407) from above, `KL ≤ ln(1 + χ²)`, and is the
one importance-sampling variance depends on.

## Decision

- **The API.**
  - Python: `chi_square_divergence(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.ChiSquareDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence: each by its own sum.
- **The value.**
  - `χ²(P‖Q) = Σᵢ (Pᵢ − Qᵢ)²/Qᵢ`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, one subtraction, the square as a product, and
    one division by `Qᵢ`; the terms are summed in order. Indices where `qᵢ = 0` and `pᵢ = 0`
    are dropped.
  - Not symmetric; zero or more, unbounded.
- **The rules.**
  - As for the Kullback–Leibler divergence: equal lengths at least 1, finite, non-negative,
    each sum above zero; `qᵢ = 0` where `pᵢ > 0` is an error, as the divergence is infinite.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the divergence exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-13`.
