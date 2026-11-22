# ADR 0566: The Rényi diversity of counts

Status: accepted, 2026-11-21.

## Context

The Rényi entropy of order `q` of a set of shares is `ln(Σ pᵢ^q)/(1 − q)`, the log of the
Hill number. `renyi_entropy` (ADR 0353) bins samples into a histogram first; this measure
takes the record as abundances, like the Hill number.

## Decision

- **The API.**
  - Python: `renyi_diversity(samples, order)` in `measurements`, giving a float in nats.
  - C#: `Measurements.RenyiDiversity(ReadOnlySpan<double> samples, double order)`.
- **The form.** The switches of the Hill number (ADR 0563), with the outer `exp` left
  off:
  - `q = 0`: `ln K`, `K` the count of values above 0.
  - `q = 1`: `−Σ pᵢ ln pᵢ`.
  - `|q − 1| < 1/2`: `log1p(Σ pᵢ·expm1((q − 1) ln pᵢ))/(1 − q)`.
  - Otherwise `(q ln m + ln Σ (pᵢ/m)^q)/(1 − q)`, `m = max pᵢ`.
  - Sums in record order. Taking `ln` of the Hill number instead would round twice.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0; otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates `ln(Σ pᵢ^q)/(1 − q)` in 60-digit
    decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
