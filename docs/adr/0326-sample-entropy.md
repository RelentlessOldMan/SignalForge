# ADR 0326: Sample entropy

Status: accepted, 2026-11-18.

## Context

Sample entropy (Richman and Moorman, 2000) asks how often two stretches of a signal that
match for `m` samples go on matching for one more. A regular signal keeps matching and scores
low; noise does not. Unlike approximate entropy it does not count a template against itself,
so short records are not biased towards regularity. It is widely used on heart-rate and
other physiological series.

## Decision

- **The API.**
  - Python: `sample_entropy(samples, m, r)` in `measurements`, giving a float.
  - C#: `Measurements.SampleEntropy(ReadOnlySpan<double> samples, int m, double r)`.
- **The value.**
  - `L = N − m` templates, `i = 0 … L−1`. Template `i` of length `k` is `x[i … i+k−1]`.
    Both lengths, `m` and `m + 1`, use the same `L` starts, so the last sample is in a
    length-`m+1` template only.
  - Two templates match when their Chebyshev distance, `max_j |x[i+j] − x[l+j]|`, is at most
    `r`. Equality counts as a match.
  - `B` counts the pairs `i < l` whose length-`m` templates match; `A` counts those whose
    length-`m+1` templates match.
  - `SampEn = −ln(A / B)`. When `A = 0` and `B > 0` it is `+∞`.
  - `r` is in the samples' units. It is not scaled by the standard deviation; a caller who
    wants `0.2·σ` passes it.
- **The rules.**
  - `samples` real, one-dimensional and finite, with `N ≥ m + 2` so there are two templates.
  - `m` an integer of at least 1.
  - `r` finite and at least 0.
  - `B = 0` (no matches at all) is an error: the value is undefined.

## Consequences

- **Cost.** All pairs are compared, `O(L²·m)`. That is fine for the few thousand samples
  these series usually have.
- **Vectors.**
  - The samples are dyadic, so every difference is exact in float and the matches do not
    depend on rounding. One case puts a distance exactly at `r`.
  - The generator counts in exact rationals and takes the logarithm in float.
  - The tolerance is `abs 1e-12, rel 1e-12`.
