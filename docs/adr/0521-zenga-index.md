# ADR 0521: The Zenga index

Status: accepted, 2026-11-20.

## Context

The Zenga index (2007) compares, at each split of the sorted holders, the mean of the
poorer part with the mean of the richer part, where the Bonferroni index (ADR 0520)
compares the poorer part with the whole. Texts give it for a continuous distribution or a
grouped table; for a record of `n` values the splits are `k = 1` to `n − 1`.

## Decision

- **The API.**
  - Python: `zenga_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.ZengaIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `Z = (1/(n − 1))·Σ_{k=1}^{n−1} (m⁺ₖ − m⁻ₖ)/m⁺ₖ`, `m⁻ₖ = Sₖ/k` the mean of the `k`
    smallest and `m⁺ₖ = (Sₙ − Sₖ)/(n − k)` the mean of the rest, `Sₖ` the running sums.
    `m⁺ₖ > 0` whenever the record is not all 0, since it holds the largest value.
  - Formed as `1 − Σ_{k<n} m⁻ₖ/m⁺ₖ/(n − 1)`, summed from `k = 1` upward in both
    languages.
  - From 0 (every value equal) to 1 (one value holds the total); at least the Bonferroni
    index, since `m⁺ₖ ≥ μ`. Unchanged when every value is scaled by the same positive
    factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0, as for the Bonferroni index.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator forms the defining sum of mean ratios exactly in rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`, as for the Bonferroni index.
