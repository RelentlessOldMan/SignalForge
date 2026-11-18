# ADR 0338: Multiscale entropy

Status: accepted, 2026-11-18.

## Context

Costa, Goldberger and Peng (2002) showed that one sample entropy (ADR 0326) can rank white
noise as more complex than 1/f noise. Looking across time scales fixes that. Multiscale entropy
computes the sample entropy of the series averaged over non-overlapping windows of growing
length, and is the usual way that measure is now reported.

## Decision

- **The API.**
  - Python: `multiscale_entropy(samples, m, r, scales)` in `measurements`, giving a float
    array with one entry per scale.
  - C#: `Measurements.MultiscaleEntropy(ReadOnlySpan<double> samples, int m, double r,
    ReadOnlySpan<int> scales)`, giving `double[]`.
- **The value.** For each scale `τ`:
  - The coarse-grained series is `y[j] = (Σ_{i=jτ}^{jτ+τ−1} x[i]) / τ` for
    `j = 0 … floor(N/τ) − 1`. The samples left at the end are not used.
  - The entry is `sample_entropy(y, m, r)` as ADR 0326 defines it, with `+∞` where no pair
    matches for `m + 1`.
  - `r` is the same at every scale, in sample units. Costa et al. fix it from the original
    series, typically `0.15·std(x)`, and that choice is left to the caller.
- **The rules.**
  - `samples` real, one-dimensional and finite. `m` and `r` as in ADR 0326.
  - `scales` not empty, each an integer of at least 1, in any order, with
    `floor(N/τ) ≥ m + 2`.
  - A scale at which no pair matches for `m` is an error, as in ADR 0326.

## Consequences

- **Vectors.**
  - The samples are small dyadic numbers, so each window sum is exact in float and each mean
    is one correctly rounded division in both languages.
  - The generator rounds the means to float in the same way, then counts the matches in
    rationals. It asserts that every comparison with `r` comes out the same in float, so
    rounding cannot flip a match.
  - The logarithms are taken in float. The tolerance is `abs 1e-13, rel 1e-12`.
