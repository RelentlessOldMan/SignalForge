# ADR 0345: Bubble entropy

Status: accepted, 2026-11-18.

## Context

Sample, approximate and fuzzy entropy (ADRs 0326, 0333, 0339) all need a tolerance `r`, and
their values depend strongly on it. Manis, Aktaruzzaman and Sassi (2017) proposed bubble
entropy, which has no tolerance and depends little on `m`. Each window is described by how
many swaps bubble sort needs to put it in order.

## Decision

- **The API.**
  - Python: `bubble_entropy(samples, m)` in `measurements`, giving a float.
  - C#: `Measurements.BubbleEntropy(ReadOnlySpan<double> samples, int m)`.
- **The value.**
  - For a window length `k`, each of the `N − k + 1` windows of `k` consecutive samples
    gets its swap count. That is the number of pairs `j < l` with `x_j > x_l`, which is what
    an ascending bubble sort swaps. Equal values are not swapped.
  - With `p_s` the share of windows with `s` swaps, `H_k = −ln Σ_s p_s²`, the Rényi entropy
    of order 2.
  - The value is `(H_{m+1} − H_m) / ln((m + 1)/(m − 1))`.
- **The rules.**
  - `samples` real, one-dimensional and finite, at least `m + 1` of them.
  - `m` an integer from 2 to 64.

## Consequences

- **Vectors.**
  - The generator counts swaps by actually running bubble sort on each window. The
    libraries count inversions, which is an independent route to the same number. The
    `Σ p²` are exact rationals, and the logarithms are taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
