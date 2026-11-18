# ADR 0325: Permutation entropy

Status: accepted, 2026-11-18.

## Context

Permutation entropy (Bandt and Pompe, 2002) measures how unpredictable a signal is from the
order of its values alone. Each run of `order` samples is reduced to the pattern that sorts
it, and the entropy of the patterns' frequencies is taken. It ignores amplitude, so a gain or
an offset does not change it. A monotone signal scores 0 and white noise close to 1.

## Decision

- **The API.**
  - Python: `permutation_entropy(samples, order, delay=1)` in `measurements`, giving a float.
  - C#: `Measurements.PermutationEntropy(ReadOnlySpan<double> samples, int order, int delay = 1)`.
- **The value.**
  - `L = N − (order − 1)·delay` windows. Window `i` is
    `v_j = x[i + j·delay]` for `j = 0 … order−1`, `i = 0 … L−1`.
  - Its pattern is the index order that sorts `v` ascending, ties kept in index order (a
    stable sort). Equal values thus count as rising.
  - `p_π` is the share of the `L` windows with pattern `π`, over the patterns that occur.
  - `H = −Σ p_π·ln p_π / ln(order!)`, from 0 to 1.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `order` an integer from 2 to 8. 8! = 40320 patterns is already far more than a usual
    record can fill.
  - `delay` an integer of at least 1.
  - `L ≥ 1`, so at least one window.

## Consequences

- **Vectors.**
  - The generator sorts each window with Python's stable `sorted`, counts the patterns
    exactly, and takes the logarithms in float.
  - The sum's order differs between implementations, so the tolerance is
    `abs 1e-12, rel 1e-12`.
