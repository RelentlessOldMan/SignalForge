# ADR 0555: The Miller–Madow entropy

Status: accepted, 2026-11-21.

## Context

The plug-in Shannon entropy `−Σ pᵢ ln pᵢ` of `N` counts falls short of the true entropy by
about `(k − 1)/(2N)` for `k` kinds (Miller 1955). Adding that term back is the
Miller–Madow estimate, the simplest bias correction.

## Decision

- **The API.**
  - Python: `miller_madow_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.MillerMadowEntropy(ReadOnlySpan<double> samples)`.
- **The value.**
  - `pᵢ = xᵢ/N`, `N = Σᵢ xᵢ` in record order. For each value above 0, in record order,
    `pᵢ ln pᵢ` is subtracted from a sum that starts at 0, and `k` counts those values.
  - `H = that sum + (k − 1)/(2N)`.
  - At least 0, and 0 when one value holds the total.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.

## Consequences

- One pass for the checks, one for the terms.
- **Vectors.**
  - The generator forms each term in 50-digit decimal.
  - The tolerance is `abs 1e-14, rel 1e-13`.
