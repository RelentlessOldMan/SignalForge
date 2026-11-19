# ADR 0348: Distribution entropy

Status: accepted, 2026-11-18.

## Context

Sample entropy (ADR 0326) reduces the distances between embedded vectors to one bit each:
closer than `r`, or not. Li, Liu and others (2015) proposed distribution entropy, which keeps
the whole distribution of those distances and needs no `r`. It is stable on short records.

Phase entropy was listed next to it in Next and was dropped. Its sectors have edges on the
axes, and any zero step puts a point exactly on one, so the two languages could assign it
to different sectors.

## Decision

- **The API.**
  - Python: `distribution_entropy(samples, m, bins=512)` in `measurements`, giving a float.
  - C#: `Measurements.DistributionEntropy(ReadOnlySpan<double> samples, int m,
    int bins = 512)`.
- **The value.**
  - The `W = N − m + 1` windows of `m` consecutive samples are compared in pairs `i < j`
    by the Chebyshev distance `d_ij`.
  - With `lo` and `hi` the smallest and largest of the distances, a distance goes in bin
    `min(M − 1, floor((d − lo)·M/(hi − lo)))`, where `M = bins`.
  - With `p_t` the share of pairs in bin `t`, the value is `−Σ p·ln p / ln M`, from 0 to 1.
  - If every distance is the same, all are in one bin and the value is 0.
- **The rules.**
  - `samples` real, one-dimensional and finite, at least `m + 1` of them, so there is at
    least one pair.
  - `m` an integer of at least 1. `bins` an integer from 2 to 1 000 000.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator takes the distances and each bin exactly in
    rationals. It asserts that no `(d − lo)·M/(hi − lo)` below `M` is within `1e-9` of an
    integer unless it is exactly one, which only happens where the float result is exact
    too. The counts are exact, and the entropy is taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
