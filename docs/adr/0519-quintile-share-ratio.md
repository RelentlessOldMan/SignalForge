# ADR 0519: The quintile share ratio

Status: accepted, 2026-11-20.

## Context

The quintile share ratio (S80/S20) is the share of a total held by the largest 20% of
holders over the share held by the smallest 20%. As for the Palma ratio (ADR 0518), the
20% and 80% can fall inside a holder; some texts weight by survey weights and round to
whole holders.

## Decision

- **The API.**
  - Python: `quintile_share_ratio(samples)` in `measurements`, giving a float.
  - C#: `Measurements.QuintileShareRatio(ReadOnlySpan<double> samples)`.
- **The value.**
  - The Lorenz curve joined by straight lines, as for the Palma ratio. With `x₍ₖ₎` the
    sorted values and `Sₖ` the running sum of the `k` smallest:
    - the smallest 20%: `n = 5j₂ + r₂` gives `low = S_{j₂} + (r₂/5)·x₍j₂₎`;
    - the smallest 80%: `4n = 5j₈ + r₈` gives `upto = S_{j₈} + (r₈/5)·x₍j₈₎`;
    - the ratio is `(Sₙ − upto)/low`.
  - At least 1; 1 when every value is equal. Unchanged when every value is scaled by the
    same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0.
  - The smallest 20% must hold some of the total: `low > 0`.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator reads the Lorenz curve at 1/5 and 4/5 in rationals, as for the Palma
    ratio.
  - The tolerance is `abs 1e-14, rel 1e-14`.
