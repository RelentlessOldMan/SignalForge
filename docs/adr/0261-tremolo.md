# ADR 0261: Tremolo

Status: accepted, 2026-11-17.

## Context

A tremolo varies a signal's gain with a slow oscillator. Unlike the ring modulator (ADR 0260),
the gain never goes negative. It swings between 1 and `1 − depth`, so the signal pulses in level
but keeps its spectrum near the original, plus sidebands at `± rate`.

## Decision

- **The API.**
  - Python: `tremolo(samples, rate, depth, sample_rate)` in `dsp`.
  - C#: `Dsp.Tremolo(samples, rate, depth, sampleRate)`.
  - Real or complex in, the same kind out.
- **The value.**
  - `c[n] = cos((2π·rate)·(n/fs))`, built as the ring modulator's carrier with phase 0.
  - `g[n] = 1 − depth·(1 − c[n])/2`, evaluated as `1 − ((depth·(1 − c))/2)`.
  - `y[n] = x[n]·g[n]`. A complex sample is scaled part by part.
  - The gain starts at 1 for `n = 0` and falls to `1 − depth` half a period later.
- **The rules.**
  - `rate` must be finite. Its sign does not matter, since cos is even.
  - `depth` must be finite, in `[0, 1]`.
  - `sample_rate` must be finite and `> 0`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the definition with the stdlib `math.cos`.
  - The fs/4 case is checked by hand: the gains are `1, 1 − d/2, 1 − d, 1 − d/2`.
  - The tolerance is `abs 1e-14`, as in ADR 0260.
