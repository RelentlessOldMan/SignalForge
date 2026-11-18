# ADR 0268: Peak normalization

Status: accepted, 2026-11-17.

## Context

Rendering a signal to a file or a DAC often starts by scaling it so its largest sample sits at a
chosen level. It is one gain, but the order of operations decides the rounding. Dividing each
sample by the peak and multiplying by the target rounds differently from multiplying by one
precomputed gain. The convention fixes a single gain.

## Decision

- **The API.**
  - Python: `normalize_peak(samples, peak=1.0)` in `dsp`.
  - C#: `Dsp.NormalizePeak(samples, peak = 1.0)`.
  - Real and complex; the output is the same kind.
- **The value.**
  - `g = peak / max|x|`, then `y = x·g`.
  - A complex sample is scaled part by part, and `|x|` is its modulus.
  - The largest `|y|` is `peak` up to rounding.
- **The rules.**
  - `peak` must be finite and `> 0`.
  - The samples must be finite and non-empty, and not all zero.

## Consequences

- **Vectors.**
  - Most real cases have power-of-two gains, so the results are exact. One has a gain of
    1/3, so `g` and `x·g` each round once.
  - Complex cases use 3-4-5 binary-fraction magnitudes, so `|x|` is exact.
  - The tolerance is `abs 1e-15, rel 1e-15`.
