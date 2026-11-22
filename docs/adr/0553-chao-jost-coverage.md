# ADR 0553: The Chao–Jost coverage

Status: accepted, 2026-11-21.

## Context

Good's coverage (ADR 0544), `1 − F₁/N`, estimates the share of the population that belongs
to kinds already seen. Chao and Jost (2012) improve it with the doubletons:
`Ĉ = 1 − F₁/N · (N − 1)F₁/((N − 1)F₁ + 2F₂)`, the estimator behind coverage-based
rarefaction.

## Decision

- **The API.**
  - Python: `chao_jost_coverage(samples)` in `measurements`, giving a float.
  - C#: `Measurements.ChaoJostCoverage(ReadOnlySpan<double> samples)`.
- **The value.**
  - `F₁` and `F₂` the numbers of values equal to 1 and to 2, `N = Σᵢ xᵢ` added in record
    order, `a = (N − 1)F₁`; `Ĉ = 1 − F₁/N · (a/(a + 2F₂))`, formed left to right.
  - 1 when there are no singletons; `1 − F₁/N`, Good's coverage, when there are no
    doubletons; from 0 to 1, and 0 only when every individual is a singleton.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.
  - `N > 1`, so `(N − 1)F₁` is not 0 when there is a singleton (otherwise
    `invalid_argument`).

## Consequences

- One pass for the checks, one for the counts.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
