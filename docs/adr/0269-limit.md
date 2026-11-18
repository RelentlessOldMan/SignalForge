# ADR 0269: Lookahead peak limiter

Status: accepted, 2026-11-17.

## Context

The compressor (ADR 0257) follows an envelope, so a fast transient gets through before the gain
drops. A peak limiter must never let `|y|` exceed the threshold. It looks ahead: the gain at
sample `n` is already low enough for the loudest sample in the next `lookahead` samples. The
gain then recovers smoothly instead of jumping back up. The output is not delayed; the
lookahead only makes the gain fall early.

## Decision

- **The API.**
  - Python: `limit(samples, threshold, lookahead, release)` in `dsp`.
  - C#: `Dsp.Limit(samples, threshold, lookahead, release)`.
  - Real and complex; the output is the same kind.
- **The value.**
  - `c[n] = min(1, T/|x[n]|)`, and `c[n] = 1` where `x[n] = 0`.
  - `a[n] = min(c[n], …, c[min(n + lookahead, N − 1)])`.
  - `g[−1] = 1`. If `a[n] < g[n−1]`, then `g[n] = a[n]`, an instant attack. Otherwise
    `g[n] = a[n] + release·(g[n−1] − a[n])`, the envelope follower's one-pole form (ADR 0238).
  - `y = x·g`; a complex sample is scaled part by part.
  - Since `g[n] ≤ a[n] ≤ c[n]`, `|y[n]| ≤ T` up to one rounding.
- **The rules.**
  - `threshold` must be finite and `> 0`.
  - `lookahead` must be an integer `≥ 0`.
  - `release` must be a finite coefficient in `[0, 1)`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from a stdlib transcription of the definition.
  - Complex magnitudes are 3-4-5 binary fractions.
  - The tolerance is `abs 1e-15, rel 1e-14`.
