# ADR 0518: The Palma ratio

Status: accepted, 2026-11-20.

## Context

The Palma ratio is the share of a total held by the largest 10% of holders over the share
held by the smallest 40%. When `n` is not a multiple of 10 the 10% and 40% fall inside a
holder; texts then differ, between rounding to whole holders and reading the Lorenz curve
(ADR 0517) between its points.

## Decision

- **The API.**
  - Python: `palma_ratio(samples)` in `measurements`, giving a float.
  - C#: `Measurements.PalmaRatio(ReadOnlySpan<double> samples)`.
- **The value.**
  - The Lorenz curve is joined by straight lines between its points `(k/n, Lₖ)`, so a
    fraction `f` of a holder counts as `f` of that holder's value. With `x₍ₖ₎` the sorted
    values and `Sₖ` the running sum of the `k` smallest:
    - the smallest 40%: `2n = 5j₄ + r₄`, `r₄` from 0 to 4, gives `low = S_{j₄} + (r₄/5)·x₍j₄₎`;
    - the smallest 90%: `9n = 10j₉ + r₉`, `r₉` from 0 to 9, gives
      `upto = S_{j₉} + (r₉/10)·x₍j₉₎`;
    - the ratio is `(Sₙ − upto)/low`. The splits are exact integer divisions, so both
      languages form the same sums.
  - Greater than 0 for a record that is not all 0; `1/4` when every value is equal.
    Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0.
  - The smallest 40% must hold some of the total: `low > 0`. An all-0 record fails this.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator reads the Lorenz curve at 2/5 and 9/10 in rationals, finding the
    segment by comparing `k/n` with the point.
  - The tolerance is `abs 1e-14, rel 1e-14`.
