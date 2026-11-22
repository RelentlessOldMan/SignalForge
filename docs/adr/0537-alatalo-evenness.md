# ADR 0537: Alatalo's evenness

Status: accepted, 2026-11-21.

## Context

Alatalo (1981) modifies Hill's ratio `N₂/N₁` (ADR 0536) to `(N₂ − 1)/(N₁ − 1)`, so that
it falls toward 0 when one holder dominates instead of rising back to 1. It is undefined
for a single positive holder, where both numbers are 1.

## Decision

- **The API.**
  - Python: `alatalo_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.AlataloEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `F = (N₂ − 1)/(N₁ − 1)`, `N₂ = 1/Σᵢ sᵢ²`, `N₁ = exp(−Σᵢ sᵢ ln sᵢ)`, `sᵢ = xᵢ/S` the
    shares, `S` added in record order, `0·ln 0 = 0`. Both sums in one pass in record
    order; formed as `(1/Σ sᵢ² − 1)/(exp(−Σ sᵢ ln sᵢ) − 1)`.
  - Above 0 and at most 1; 1 when every positive value is equal. Zero shares do not change
    it.
- **The rules.**
  - A real, finite, one-dimensional record, every value at least 0, with at least 2
    positive shares (fewer is `invalid_argument`).

## Consequences

- One pass for the total, one for both sums; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the logarithms and exponential in 50-digit
    `decimal`.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `log` and `exp` in each language; the
    subtraction of 1 loses digits only near a single dominant share.
