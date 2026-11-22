# ADR 0560: The Bonachela entropy

Status: accepted, 2026-11-21.

## Context

Bonachela, Hinrichsen and Muñoz (2008) give an entropy estimate built to balance bias
against variance for small samples:
`H = (1/(N + 2)) Σᵢ (xᵢ + 1) Σ_{j = xᵢ + 2}^{N + 2} 1/j`, the outer sum over the kinds seen.

## Decision

- **The API.**
  - Python: `bonachela_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.BonachelaEntropy(ReadOnlySpan<double> samples)`.
- **The value.**
  - `h(m) = Σ_{j=1}^{m} 1/j` over ascending `j`, formed once up to `N + 2`, keeping
    `h(xᵢ + 1)` on the way for each value above 0.
  - `A = Σ (xᵢ + 1)(h(N + 2) − h(xᵢ + 1))` over values above 0 in record order, and
    `H = A/(N + 2)`.
  - Above 0: one kind gives `(N + 1)/(N + 2)²`, not 0.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.

## Consequences

- One pass of `N + 2` steps for the harmonic numbers, then one over the record.
- **Vectors.**
  - The generator sums each inner range directly, in exact rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`.
