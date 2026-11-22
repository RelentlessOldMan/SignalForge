# ADR 0545: The Chao1 richness

Status: accepted, 2026-11-21.

## Context

Chao (1984) estimates the number of kinds in a population from the kinds seen and the
numbers of singletons `F₁` and doubletons `F₂`. The classic form `k + F₁²/(2F₂)` is
undefined without doubletons; the bias-corrected form `k + F₁(F₁ − 1)/(2(F₂ + 1))` (Chao
2005) is always defined, and is the one here.

## Decision

- **The API.**
  - Python: `chao1_richness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.Chao1Richness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `S = k + F₁(F₁ − 1)/(2(F₂ + 1))`, `k` the number of values above 0, `F₁` and `F₂` the
    numbers of values exactly equal to 1 and to 2. Only those three counts are used.
  - At least `k`, and `k` when there are fewer than 2 singletons.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- One pass for the checks, one for the counts.
- **Vectors.**
  - The generator forms the value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`, for one division.
