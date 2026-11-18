# ADR 0328: Modified Allan deviation

Status: accepted, 2026-11-18.

## Context

The Allan deviation (ADR 0327) falls as `1/τ` for both white and flicker phase noise, so it
cannot tell them apart. The modified Allan deviation adds one more average over `m` adjacent
starts. That changes the slope for white phase noise to `τ^(−3/2)` while flicker phase noise
stays near `1/τ`. The definition follows the time-and-frequency literature (for example NIST
Special Publication 1065, from fractional-frequency data).

## Decision

- **The API.**
  - Python: `modified_allan_deviation(fractional_frequency, sample_interval,
    averaging_factors)` in `measurements`, giving the same `AllanDeviation(taus, deviations)`
    as ADR 0327.
  - C#: `Measurements.ModifiedAllanDeviation`, same arguments, giving the record
    `AllanDeviation`.
- **The value.** For each averaging factor `m`, in the order given:
  - `ȳ_k` is the direct mean of `y[k … k+m−1]`, as in ADR 0327.
  - `d_i = ȳ_{i+m} − ȳ_i`, `i = 0 … M−2m`.
  - `S_j = Σ_{i=j}^{j+m−1} d_i`, `j = 0 … M−3m+1`.
  - `σ² = Σ_j S_j² / (2·m²·(M − 3m + 2))`.
  - This equals the literature's triple sum
    `Σ_j [Σ_{i=j}^{j+m−1} Σ_{k=i}^{i+m−1} (y[k+m] − y[k])]² / (2·m⁴·(M − 3m + 2))`, because
    the inner sum is `m·d_i`.
  - `τ = m·τ₀`. At `m = 1` it equals the Allan deviation.
- **The rules.**
  - As ADR 0327, except that each factor needs `3m ≤ M + 1`, so that there is at least one
    `S_j`.

## Consequences

- **Checks.** A linear drift `y = D·i·τ₀` gives `σ = D·τ/√2`, as for the Allan deviation. The
  Python tests also compare against the triple sum written out literally.
- **Vectors.**
  - The generator evaluates the triple sum exactly in rationals from dyadic samples. It takes
    one float square root.
  - The tolerance is `abs 1e-15, rel 1e-12`.
