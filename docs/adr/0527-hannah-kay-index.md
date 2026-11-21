# ADR 0527: The Hannah–Kay index

Status: accepted, 2026-11-21.

## Context

Hannah and Kay (1977) give a family of concentration measures as a numbers equivalent: how
many equal holders would give the same concentration. The parameter `α` sets how much the
large shares weigh. Some texts give the reciprocal (a concentration from `1/n` to 1)
instead; the numbers equivalent is the exponential of the Rényi entropy of the shares.

## Decision

- **The API.**
  - Python: `hannah_kay_index(samples, alpha)` in `measurements`, giving a float.
  - C#: `Measurements.HannahKayIndex(ReadOnlySpan<double> samples, double alpha)`.
- **The value.**
  - `HK(α) = (Σᵢ sᵢ^α)^(1/(1 − α))`, `sᵢ = xᵢ/S` the shares, `S` added in record order;
    at `α = 1` exactly, the limit `exp(−Σᵢ sᵢ ln sᵢ)` with `0·ln 0 = 0`. The numbers
    equivalent, not its reciprocal.
  - The powers are the platform `pow` (`math.pow`, `Math.Pow`) and added in record order.
  - From 1 (one value holds the total) to `n` (every value equal). Never rises as `α`
    grows. `HK(2)` is one over the Herfindahl index (ADR 0523).
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.
  - `α` finite and above 0.

## Consequences

- One pass for the total, one for the powers; no sort.
- **Vectors.**
  - The generator forms the shares exactly and the powers, logarithms and roots in
    50-digit `decimal`; at `α = 2` and on equal shares the values are exact.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `pow` and `log` in each language.
