# ADR 0526: The Kwoka dominance index

Status: accepted, 2026-11-21.

## Context

Kwoka (1977) measures how far each holder stands above the next: the sum of the squared
gaps between neighbouring shares ranked from the largest. Some texts stop at a fixed
number of leading holders; here every neighbouring pair counts.

## Decision

- **The API.**
  - Python: `kwoka_dominance_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.KwokaDominanceIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `D = Σ_{r=1}^{n−1} (s₍ᵣ₎ − s₍ᵣ₊₁₎)²`, `s₍ᵣ₎` the shares of the total ranked from the
    largest. Each gap is formed as `(x₍ᵣ₎ − x₍ᵣ₊₁₎)/S`, `S` the total added in record order,
    and the squares added from the largest pair down.
  - 0 when every value is equal or there is one value; 1 when one of at least 2 values
    holds the total. At most the square of the largest share, so at most the Herfindahl
    index. Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator ranks dyadic shares from the largest and sums the squared gaps exactly
    in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
