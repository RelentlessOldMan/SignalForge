# ADR 0561: Zhang's entropy

Status: accepted, 2026-11-21.

## Context

Zhang (2012) gives an estimate of the Shannon entropy of counts whose bias falls faster
than any power of `1/N`:
`H = Σ_{v=1}^{N−1} (1/v) Σᵢ pᵢ Π_{j=0}^{v−1}(1 − (xᵢ − 1)/(N − 1 − j))`. The factor at
`j = N − xᵢ` is 0, so each kind's inner sum stops at `v = N − xᵢ`.

## Decision

- **The API.**
  - Python: `zhang_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.ZhangEntropy(ReadOnlySpan<double> samples)`.
- **The value.**
  - For a value `x` above 0: `P = 1`, `T = 0`, then for `v = 1, …, N − x` in order,
    `P ← P · (1 − (x − 1)/(N − v))` and `T ← T + P/v`.
  - `T` depends only on `x`, so it is formed once for each distinct value.
  - `H = Σ (xᵢ/N) · T(xᵢ)` over values above 0 in record order; 0 when one value holds the
    total.
- **The rules.**
  - Whole numbers, as for the Brillouin index but totalling at most 10 000: real, finite,
    one-dimensional, at least 1 value, every value at least 0 and whole, not all 0.
  - `N > 1` (otherwise `invalid_argument`).
  - The lower cap bounds the work: at most about `√(2N)` distinct values, each up to `N`
    steps.

## Consequences

- **Vectors.**
  - The generator runs the definition's product and sum to `v = N − 1` in exact
    rationals, without the early stop.
  - The tolerance is `abs 1e-13, rel 1e-12`.
