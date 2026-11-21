# ADR 0524: The concentration ratio

Status: accepted, 2026-11-21.

## Context

The concentration ratio `CRₖ` is the share of a total held by the `k` largest holders,
used beside the Herfindahl index (ADR 0523). Texts give it as a fraction or a percentage.

## Decision

- **The API.**
  - Python: `concentration_ratio(samples, k)` in `measurements`, giving a float.
  - C#: `Measurements.ConcentrationRatio(ReadOnlySpan<double> samples, int k)`.
  - The count is named `k`, as in `CRₖ`; Next had called it `count`, which in Python
    would hide the argument check of that name.
- **The value.**
  - `CRₖ = (x₍ₙ₋₁₎ + … + x₍ₙ₋ₖ₎)/S`: the `k` largest added from the largest down, over the
    total `S` added in record order. A fraction, not a percentage.
  - From `k/n` to 1; 1 when `k = n`. Never falls as `k` grows. `CR₁` is at least the
    Herfindahl index.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.
  - `k` a whole number from 1 to `n`. In Python a float or bool is refused, as for every
    count.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator sums the `k` largest exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
