# ADR 0258: Downward expander

Status: accepted, 2026-11-17.

## Context

ADR 0257 joins the envelope follower (ADR 0238) to the compressor gain (ADR 0254). A downward
expander is the same chain with the expander gain (ADR 0256). It pushes quiet passages further
down, as a softer noise gate (ADR 0255).

## Decision

- **The API.**
  - Python: `expand(samples, threshold_db, ratio, attack, release, *, knee_db=0.0,
    makeup_db=0.0)` in `dsp`.
  - C#: `Dsp.Expand(samples, thresholdDb, ratio, attack, release, kneeDb = 0, makeupDb = 0)`.
  - Real or complex in, the same kind out.
- **The value.** The same as ADR 0257, with `g[n]` the expander gain of ADR 0256 at
  `L[n] = 20·log10(e[n])`.
  - If `e[n] = 0`, then `g[n] = 0`. This changes nothing, because `e[n] = 0` only when
    `x[n] = 0`.
  - A very low level can make `10^(g/20)` underflow to 0, which mutes the sample.
- **The rules.** The same as ADR 0257.

## Consequences

- **Vectors.**
  - The generator runs the envelope in exact rationals and the rest in stdlib floats.
  - It checks the instant cases against the closed form `|y| = 10^(T/20)·(|x|/10^(T/20))^ratio`
    below the threshold.
  - The tolerance is `rel 1e-12`, as in ADR 0257.
- **C#.** The compressor and the expander share one private helper. It turns an envelope into
  per-sample factors through a gain function.
