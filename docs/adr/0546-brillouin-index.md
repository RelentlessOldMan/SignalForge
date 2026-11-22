# ADR 0546: The Brillouin index

Status: accepted, 2026-11-21.

## Context

Brillouin (1956) measures the information in a fully counted collection as
`HB = (ln N! − Σᵢ ln xᵢ!)/N`, the logarithm of the number of ways to arrange the `N`
individuals into kinds of the given sizes, per individual. It needs whole-number counts.

## Decision

- **The API.**
  - Python: `brillouin_index(samples)` in `measurements`, giving a float, in nats.
  - C#: `Measurements.BrillouinIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `HB = (ln N! − Σᵢ ln xᵢ!)/N`, `N = Σᵢ xᵢ` added in record order. Each `ln m!` is the
    sum of `ln j` for `j` from 2 to `m` in that order, so both languages add the same
    terms; the terms of `Σᵢ ln xᵢ!` are added in record order, value by value.
  - At least 0, and 0 when one value holds the total. Below the Shannon entropy of the
    shares, which it approaches as the counts grow.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value a whole
    number at least 0, not all 0.
  - `N` at most 10 000 000, as the work is `O(N)`; larger is `invalid_argument`.

## Consequences

- No gamma function is needed (C# has none); the work grows with `N`.
- **Vectors.**
  - The generator forms the multinomial coefficient `N!/Π xᵢ!` exactly as an integer and
    its logarithm in 50-digit `decimal`.
  - The tolerance is `abs 1e-13, rel 1e-12`: the difference of two sums of logarithms
    cancels, and the sums are long.
