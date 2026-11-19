# ADR 0414: The Jeffreys divergence

Status: accepted, 2026-11-19.

## Context

The Jeffreys divergence is the Kullback–Leibler divergence (ADR 0407) taken both ways and
added: `KL(P‖Q) + KL(Q‖P)`. It is symmetric, which the Kullback–Leibler divergence is not,
and is the form used where neither distribution is the reference, as in comparing two
measured spectra.

## Decision

- **The API.**
  - Python: `jeffreys_divergence(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.JeffreysDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - Normalized as for the Kullback–Leibler divergence: each by its own sum.
- **The value.**
  - `J(P, Q) = Σᵢ (Pᵢ − Qᵢ)·ln(Pᵢ/Qᵢ)`, which equals the two divergences added.
  - `Pᵢ` and `Qᵢ` as in ADR 0407. Per index, one subtraction, one division and one log;
    the terms are summed in order. Indices where both are zero are dropped.
  - Each term is zero or more in floating point too (the difference and the log have the
    same sign), so no clamp is needed.
- **The rules.**
  - As for the Kullback–Leibler divergence: equal lengths at least 1, finite, non-negative,
    each sum above zero.
  - An index where exactly one of `pᵢ` and `qᵢ` is zero is an error: one of the two
    divergences is infinite.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms the distributions exactly in rationals and the logarithms in
    40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
