# ADR 0413: The Rényi divergence

Status: accepted, 2026-11-19.

## Context

The Rényi divergence of order `α` is a family that holds several of the divergences already
built: `α = ½` gives twice the Bhattacharyya distance (ADR 0410), `α = 2` gives
`ln(1 + χ²)` (ADR 0412), and the limit `α → 1` gives the Kullback–Leibler divergence
(ADR 0407). It is used in privacy accounting and in bounds on hypothesis tests.

## Decision

- **The API.**
  - Python: `renyi_divergence(p, q, alpha)` in `measurements`, giving a float.
  - C#: `Measurements.RenyiDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q,
    double alpha)`.
  - Normalized as for the Kullback–Leibler divergence: each by its own sum.
- **The value.**
  - `D_α(P‖Q) = ln(Σᵢ Pᵢ^α·Qᵢ^(1−α))/(α − 1)`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Indices with `pᵢ = 0` are dropped; for `α < 1`, so are
    indices with `qᵢ = 0`. Per index, `pow(Pᵢ, α)·pow(Qᵢ, 1 − α)`; the terms are summed in
    order, then the log is divided by `α − 1`, and a result below zero is `0`.
  - `α = 1` is not taken: the Kullback–Leibler divergence is its own function.
- **The rules.**
  - `alpha` is finite, above 0 and not 1.
  - `p` and `q` as for the Kullback–Leibler divergence: equal lengths at least 1, finite,
    non-negative, each sum above zero.
  - For `α > 1`, `qᵢ = 0` where `pᵢ > 0` is an error. For `α < 1`, a sum of zero (no index
    where both are positive) is an error. Either way the divergence is infinite.

## Consequences

- The cost is one pass for the sums and one for the terms, two powers per index.
- **Vectors.**
  - The generator forms the distributions exactly in rationals, the powers and the logarithm
    in 40-digit decimal.
  - The tolerance is `abs 1e-14, rel 1e-12`: each power may differ in the last place between
    the two languages' maths libraries.
