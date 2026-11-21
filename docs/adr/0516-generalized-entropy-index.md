# ADR 0516: The generalized entropy index

Status: accepted, 2026-11-20.

## Context

The generalized entropy family `GE(α)` holds the inequality measures that split exactly
into a part within groups and a part between them. Its parameter `α` sets which part of
the range weighs most: low `α` the bottom, high `α` the top. The mean log deviation
(ADR 0514) is `GE(0)`, the Theil index (ADR 0511) is `GE(1)`, and half the squared
coefficient of variation (ADR 0513) is `GE(2)`.

## Decision

- **The API.**
  - Python: `generalized_entropy_index(samples, alpha)` in `measurements`, giving a
    float.
  - C#: `Measurements.GeneralizedEntropyIndex(ReadOnlySpan<double> samples,
    double alpha)`.
- **The value.**
  - With `rᵢ = xᵢ/μ`, `μ` the mean: `GE(α) = (1/(n·α(α − 1)))·Σ (rᵢ^α − 1)` for `α` not
    0 or 1; `GE(0) = −(1/n)·Σ ln rᵢ`; `GE(1) = (1/n)·Σ rᵢ·ln rᵢ`, the two limits.
  - At least 0; 0 when every value is equal. Unchanged when every value is scaled by the
    same positive factor.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value greater than
    0, as for the mean log deviation.
  - `α` any finite real.

## Consequences

- The cost is two passes and a power per value. Near `α = 0` or `α = 1` the general form
  loses digits to cancellation; only the exact values 0 and 1 take the limit forms.
- **Vectors.**
  - The generator takes each ratio to the mean exactly in rationals, and each power as
    `exp(α·ln r)` in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-13`.
