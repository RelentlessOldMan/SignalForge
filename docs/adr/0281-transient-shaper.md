# ADR 0281: Transient shaper

Status: accepted, 2026-11-17.

## Context

A transient shaper raises or lowers the attack of each note without a threshold. It compares a
fast envelope with a slow one. At an onset the fast one rises first, so their ratio is above 1.
During the sustain the two meet, so the ratio is 1. Raising the ratio to a power and applying it
as a gain sharpens the attacks (power above 0) or softens them (power below 0). It is built on
the envelope follower (ADR 0238).

## Decision

- **The API.**
  - Python: `transient_shaper(samples, fast, slow, amount)` in `dsp`.
  - C#: `Dsp.TransientShaper(samples, fast, slow, amount)`.
  - Real and complex; the output is the same kind.
- **The envelopes.**
  - `ef = envelope_follower(samples, fast, fast)`.
  - `es = envelope_follower(samples, slow, slow)`.
  - Each uses one coefficient for both attack and release.
- **The gain.**
  - `g[n] = (ef[n]/es[n])^amount`, the ratio taken first.
  - `g[n] = 1` where either envelope is 0. An envelope is 0 only where the sample is 0, so this
    only avoids `0·∞`.
- **The value.** `y[n] = x[n]·g[n]`; complex part by part.
- **The rules.**
  - `fast` and `slow` must be finite and in `[0, 1)`. Neither has to be the smaller; swapping
    them inverts the effect.
  - `amount` must be finite; 0 returns the input.
  - The samples must be finite and at least one.

## Consequences

- **Vectors.**
  - Expected values come from the envelopes computed in exact rationals and rounded to floats,
    as the implementations hold them.
  - The gain is the stdlib `**` of their float ratio.
  - The tolerance is `abs 1e-14, rel 1e-12`.
