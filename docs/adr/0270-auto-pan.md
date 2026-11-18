# ADR 0270: Auto-panner

Status: accepted, 2026-11-17.

## Context

An auto-panner moves a mono source between the speakers under a low-frequency oscillator. It is
the panner (ADR 0265) with a position that changes each sample. Its cosine is built the same way
as the ring modulator and tremolo carrier (ADR 0260), so all three share one convention.

## Decision

- **The API.**
  - Python: `auto_pan(samples, rate, depth, sample_rate, *, law="constant_power")` in `dsp`
    returns `LeftRight`.
  - C#: `Dsp.AutoPan(samples, rate, depth, sampleRate, law = PanLaw.ConstantPower)`.
  - Real samples only.
- **The value.**
  - `p[n] = depth·cos((2π·rate)·(n/fs))`, evaluated in that order.
  - The gains at `p[n]` follow the panner's law:
    - constant power: `θ = (p + 1)·(π/4)`, `gL = cos θ`, `gR = sin θ`;
    - linear: `gL = (1 − p)/2`, `gR = (1 + p)/2`.
  - `left = x·gL`, `right = x·gR`.
  - At `n = 0` the source is at `depth`, toward the right for `depth > 0`.
- **The rules.**
  - `rate` must be finite.
  - `depth` must be in `[0, 1]`.
  - `sample_rate` must be finite and `> 0`.
  - `law` must be one of the panner's names.
  - The samples must be real, finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the stdlib `math.cos` and `math.sin`.
  - They pass through two transcendental calls, so the tolerance is `abs 1e-14, rel 1e-14`.
