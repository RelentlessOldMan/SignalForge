# ADR 0216: Inverse sine coefficients

Status: accepted, 2026-11-17. It is another form of the reflection coefficients, beside the
log-area ratios of ADR 0215.

## Context

Some speech coders quantize `θ = arcsin k` rather than `k` or the log-area ratio. The arcsine
also stretches the region near `|k| = 1`, but `θ` stays bounded, which suits fixed-range
quantizers.

## Decision

- **The API.**
  - Python: `reflection_to_arcsine(reflection)` and `arcsine_to_reflection(arcsine)` in `dsp`.
  - C#: `Dsp.ReflectionToArcsine` and `Dsp.ArcsineToReflection`.
  - They are real only.
- **The values.** `θ = arcsin k`, in radians, and the inverse is `k = sin θ`.
- **The rules.**
  - Both inputs must be finite, real and non-empty.
  - Every `k` must have `|k| < 1`, and every `θ` must have `|θ| < π/2`. Together these keep the
    map one-to-one and the filter minimum phase.

## Consequences

- **Vectors.** The expected values are the closed forms `k = 1/2 → π/6`, `√2/2 → π/4` and
  `√3/2 → π/3`, with their negatives and 0.
