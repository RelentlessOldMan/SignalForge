# ADR 0333: Approximate entropy

Status: accepted, 2026-11-18.

## Context

Approximate entropy (Pincus, 1991) came before sample entropy (ADR 0326) and is still widely
reported, in heart-rate work in particular. It counts each template as matching itself, which
keeps every logarithm finite even on short records. The cost is a bias toward regularity.
Users comparing with published values need it as Pincus defined it.

## Decision

- **The API.**
  - Python: `approximate_entropy(samples, m, r)` in `measurements`, giving a float.
  - C#: `Measurements.ApproximateEntropy(ReadOnlySpan<double> samples, int m, double r)`.
- **The value.** With `N` samples, for a template length `k`:
  - There are `n_k = N − k + 1` templates `x[i … i+k−1]`.
  - `C_i^k` is the number of templates `j` (`i` itself included) with
    `max_l |x[j+l] − x[i+l]| ≤ r`, divided by `n_k`.
  - `Φ_k = (1/n_k)·Σ_i ln C_i^k`.
  - The approximate entropy is `Φ_m − Φ_{m+1}`.
- **The rules.**
  - `samples` real, one-dimensional, finite and at least `m + 2` long.
  - `m` an integer of at least 1. `r` real, finite and at least 0, in sample units, as in
    ADR 0326.
  - The value is always defined, because the self-matches keep every `C_i^k > 0`.

## Consequences

- **Vectors.**
  - The samples and `r` are dyadic, so every distance and comparison is exact in float and
    the match counts are exact integers. The generator counts them in rationals and takes the
    logarithms in float.
  - A constant gives exactly 0.
  - The tolerance is `abs 1e-13, rel 1e-12`.
