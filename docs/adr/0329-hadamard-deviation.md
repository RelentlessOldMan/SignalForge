# ADR 0329: Hadamard deviation

Status: accepted, 2026-11-18.

## Context

A steady frequency drift dominates the Allan deviation at long averaging times: it gives
`D·τ/√2` (ADR 0327) and hides the noise underneath. The Hadamard deviation uses second
differences of the averaged frequencies, so a linear drift cancels exactly. It also converges
for the random-walk and flicker-walk frequency noises that rubidium clocks and GNSS clocks
show. The overlapping estimator follows the time-and-frequency literature (for example NIST
Special Publication 1065, from fractional-frequency data).

## Decision

- **The API.**
  - Python: `hadamard_deviation(fractional_frequency, sample_interval, averaging_factors)` in
    `measurements`, giving `AllanDeviation(taus, deviations)` (ADR 0327).
  - C#: `Measurements.HadamardDeviation`, same arguments, giving the record `AllanDeviation`.
- **The value.** For each averaging factor `m`, in the order given:
  - `ȳ_k` is the direct mean of `y[k … k+m−1]`, as in ADR 0327.
  - `σ² = Σ_{j=0}^{M−3m} (ȳ_{j+2m} − 2·ȳ_{j+m} + ȳ_j)² / (6·(M − 3m + 1))`.
  - Each second difference is computed as `(ȳ_{j+2m} − ȳ_{j+m}) − (ȳ_{j+m} − ȳ_j)`.
  - `τ = m·τ₀`.
- **The rules.**
  - As ADR 0327, except that each factor needs `3m ≤ M`.

## Consequences

- **Checks.** A linear drift gives 0, up to rounding. White frequency noise of variance `s²`
  gives `σ² ≈ s²/m`, the same as the Allan variance.
- **Vectors.**
  - The generator evaluates the sum exactly in rationals from dyadic samples. It takes one
    float square root.
  - The tolerance is `abs 1e-15, rel 1e-12`.
