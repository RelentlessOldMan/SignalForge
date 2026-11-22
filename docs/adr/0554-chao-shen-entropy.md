# ADR 0554: The Chao–Shen entropy

Status: accepted, 2026-11-21.

## Context

The plug-in Shannon entropy of counts is biased low: kinds not seen add nothing. Chao and
Shen (2003) scale the shares by the sample coverage `C = 1 − F₁/N` and weight each term by
the chance `1 − (1 − C pᵢ)^N` that its kind was seen at all, a Horvitz–Thompson estimate:
`H = −Σᵢ C pᵢ ln(C pᵢ)/(1 − (1 − C pᵢ)^N)`.

## Decision

- **The API.**
  - Python: `chao_shen_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.ChaoShenEntropy(ReadOnlySpan<double> samples)`.
- **The value.**
  - `F₁` the number of values equal to 1, taken as `N − 1` when it equals `N` (every
    individual a singleton) so that `C > 0`; `C = 1 − F₁/N`, `N = Σᵢ xᵢ` in record order.
  - For each value above 0, in record order, `aᵢ = C · (xᵢ/N)` and the term
    `aᵢ ln(aᵢ)/(1 − (1 − aᵢ)^N)`, the power taken as a real power; `H` is 0 less the terms,
    subtracted one at a time.
  - At least 0, and 0 when one value holds the total.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.

## Consequences

- One pass for the checks, one for the singletons, one for the terms.
- **Vectors.**
  - The generator forms each term in 50-digit decimal, the power exactly as an integer
    power.
  - The tolerance is `abs 1e-13, rel 1e-12`, for the logarithms and powers.
