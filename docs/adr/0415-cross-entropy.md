# ADR 0415: The cross-entropy

Status: accepted, 2026-11-19.

## Context

The cross-entropy of `Q` under `P` is the mean code length, in nats, of symbols drawn from
`P` and coded for `Q`: the entropy of `P` plus the Kullback–Leibler divergence (ADR 0407).
It is the usual loss for a classifier's output against a label distribution.

## Decision

- **The API.**
  - Python: `cross_entropy(p, q)` in `measurements`, giving a float in nats.
  - C#: `Measurements.CrossEntropy(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence: each by its own sum.
- **The value.**
  - `H(P, Q) = −Σᵢ Pᵢ·ln Qᵢ`.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Indices with `pᵢ = 0` are dropped. Per index, one log and
    one product; the terms are summed in order, then `0 − sum` (so a point mass on a point
    mass gives `+0`).
  - Not symmetric; zero or more, unbounded.
- **The rules.**
  - As for the Kullback–Leibler divergence: equal lengths at least 1, finite, non-negative,
    each sum above zero; `qᵢ = 0` where `pᵢ > 0` is an error, as the value is infinite.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distributions exactly in rationals and the logarithms in
    40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
