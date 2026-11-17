# ADR 0215: Log-area ratios

Status: accepted, 2026-11-17. It is another form of the reflection coefficients of ADR 0210.

## Context

Speech coders quantize reflection coefficients as log-area ratios. Near `|k| = 1`, where the
spectrum is most sensitive, a uniform quantizer in `k` is poor. The log-area ratio stretches
that region.

## Decision

- **The API.**
  - Python: `reflection_to_lar(reflection)` and `lar_to_reflection(lar)` in `dsp`.
  - C#: `Dsp.ReflectionToLar` and `Dsp.LarToReflection`.
  - They are real only, since the log-area ratio is defined for real `k`.
- **The values.**
  - `g = ln((1 + k)/(1 − k))`, computed as `2·atanh(k)`.
  - The inverse is `k = tanh(g/2)`.
  - The sign follows `k`.
- **The rules.**
  - Both inputs must be finite, real and non-empty.
  - Every `k` must have `|k| < 1`.
  - Any finite `g` is allowed. A very large `|g|` rounds `k` to `±1`.

## Consequences

- **Vectors.** The expected values are closed forms: `k = 1/3 → ln 2`, `3/5 → ln 4`,
  `4/5 → ln 9` and `9/10 → ln 19`. The inverse cases use these, and `tanh` of the stdlib for a
  large `g`.
