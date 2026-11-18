# ADR 0331: Time deviation

Status: accepted, 2026-11-18.

## Context

Telecom timing work (network synchronization masks, for example) states stability as the
time deviation, TDEV, in seconds rather than as a dimensionless frequency deviation. It is the
modified Allan deviation (ADR 0328) scaled by `τ/√3`. For white phase noise it equals the
standard deviation of the time error averaged over `τ`, which is why the factor is `√3`.

## Decision

- **The API.**
  - Python: `time_deviation(fractional_frequency, sample_interval, averaging_factors)` in
    `measurements`, giving `AllanDeviation(taus, deviations)` (ADR 0327) with the deviations
    in seconds.
  - C#: `Measurements.TimeDeviation`, same arguments, giving the record `AllanDeviation`.
- **The value.** For each averaging factor `m`, `τ = m·τ₀` and
  `TDEV = (τ / √3)·MDEV(τ)`, MDEV as ADR 0328 defines it.
- **The rules.** As ADR 0328: each factor needs `1 ≤ m` and `3m ≤ M + 1`.

## Consequences

- **Vectors.**
  - The generator evaluates `τ²·Mod σ²/3` exactly in rationals, from the literature's triple
    sum on dyadic samples. It takes one float square root.
  - The tolerance is `abs 1e-18, rel 1e-12`. The deviations are small numbers of seconds.
