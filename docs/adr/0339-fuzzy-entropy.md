# ADR 0339: Fuzzy entropy

Status: accepted, 2026-11-18.

## Context

Sample entropy (ADR 0326) counts a template pair as matching or not, so its value jumps as
distances cross `r`, and a short record can leave it undefined. Chen, Wang, Xie and Yu (2007)
replaced the hard threshold with a smooth membership function. They also removed each
template's own mean, so that a slow trend is not read as structure. Fuzzy entropy is defined
for any record and changes smoothly with `r`.

## Decision

- **The API.**
  - Python: `fuzzy_entropy(samples, m, r, n=2)` in `measurements`, giving a float.
  - C#: `Measurements.FuzzyEntropy(ReadOnlySpan<double> samples, int m, double r,
    double n = 2)`.
- **The value.** With `N` samples and `M = N − m` templates for both lengths, as in Chen et
  al.:
  - For `k = m` and `k = m + 1`, template `i < M` is `X_i[l] = x[i+l] − mean(x[i … i+k−1])`
    for `l < k`.
  - `d_ij = max_l |X_i[l] − X_j[l]|` and `D_ij = exp(−d_ij^n / r)`.
  - `φ_k = (1/M)·Σ_i (1/(M − 1))·Σ_{j≠i} D_ij`.
  - The fuzzy entropy is `ln φ_m − ln φ_{m+1}`.
- **The rules.**
  - `samples` real, one-dimensional, finite and at least `m + 2` long.
  - `m` an integer of at least 1. `r` finite and above 0. `n` finite and at least 1.
  - Some papers allow `n < 1`, but that power is ill-conditioned. `dⁿ` then has an
    infinite slope at 0, so the rounding of a baseline-removed distance that is exactly 0,
    about 1e-16, grows to about 1e-8 at `n = 0.5`. The two languages would not agree.
  - The value is always defined, because every `D_ij > 0` unless `exp` underflows. If a `φ`
    does reach 0 that way, it is an error.

## Consequences

- **Vectors.**
  - The generator removes the baselines and takes the distances exactly in rationals from
    dyadic samples. The powers, `exp` and the logarithms are taken in float.
  - A straight line gives identical templates after the baseline is removed, so its value
    is exactly 0, which the generator asserts.
  - The tolerance is `abs 1e-12, rel 1e-11`.
