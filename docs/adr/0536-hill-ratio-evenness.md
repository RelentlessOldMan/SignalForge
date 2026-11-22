# ADR 0536: The Hill ratio evenness

Status: accepted, 2026-11-21.

## Context

Hill (1973) proposes evenness as a ratio of his numbers of different orders; the common
choice is `E₂,₁ = N₂/N₁`, the inverse Simpson index over the exponential of the Shannon
entropy. It does not depend on `n`, so zero shares do not change it. Like the measure
itself, it gives 1 for a single holder as well as for equal holders.

## Decision

- **The API.**
  - Python: `hill_ratio_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.HillRatioEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = N₂/N₁`, `N₂ = 1/Σᵢ sᵢ²`, `N₁ = exp(−Σᵢ sᵢ ln sᵢ)`, `sᵢ = xᵢ/S` the shares, `S`
    added in record order, `0·ln 0 = 0`. Both sums in one pass in record order; formed as
    `(1/Σ sᵢ²)/exp(−Σ sᵢ ln sᵢ)`.
  - Above 0 and at most 1, as `N₂ ≤ N₁`; 1 when every positive value is equal.
    `E = HK(2)/HK(1)`, `HK` the Hannah–Kay index (ADR 0527).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the total, one for both sums; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the logarithms and exponential in 50-digit
    `decimal`.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `log` and `exp` in each language.
