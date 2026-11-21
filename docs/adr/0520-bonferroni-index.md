# ADR 0520: The Bonferroni index

Status: accepted, 2026-11-20.

## Context

The Bonferroni index compares the mean of the poorest `k` holders with the overall mean,
for every `k`. It weights gaps at the bottom more than the Gini coefficient (ADR 0510)
does. Texts differ on whether the `k = n` term, which is always 0, is counted: with it the
divisor is `n`, without it `n − 1`.

## Decision

- **The API.**
  - Python: `bonferroni_index(samples)` in `measurements`, giving a float.
  - C#: `Measurements.BonferroniIndex(ReadOnlySpan<double> samples)`.
- **The value.**
  - `B = (1/(n − 1))·Σ_{k=1}^{n−1} (μ − mₖ)/μ`, `μ` the mean and `mₖ = Sₖ/k` the mean of
    the `k` smallest, `Sₖ` their running sum. The `k = n` term is left out, so `B` runs
    from 0 (every value equal) to 1 (one value holds the total).
  - Formed as `1 − n·Σ_{k<n} (Sₖ/k)/((n − 1)·Sₙ)`, the sum added from `k = 1` upward in
    both languages.
  - Unchanged when every value is scaled by the same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 2 values, every value at least 0,
    not all 0.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator forms the defining sum of mean gaps exactly in rationals.
  - The tolerance is `abs 1e-14, rel 1e-13`, as `1 − ...` loses a few bits.
