# ADR 0295: Schroeder reverberator

Status: accepted, 2026-11-17.

## Context

Schroeder's reverberator (1962) is the base of most algorithmic reverbs. Parallel feedback
combs with mutually prime delays build a dense train of echoes that decays, and series
all-passes smear the train into a diffuse tail without colouring its spectrum. The parts exist:
the feedback comb (ADR 0237) and the Schroeder all-pass (ADR 0240). This chains them, with the
delays and gains left to the caller.

## Decision

- **The API.**
  - Python: `schroeder_reverb(samples, combs, comb_gains, allpasses, allpass_gain, mix)` in
    `dsp`.
  - C#: `Dsp.SchroederReverb(samples, combs, combGains, allpasses, allpassGain, mix)`.
  - `combs` and `allpasses` are lists of integer delays in samples.
  - Real samples only.
- **The value.**
  - `w = (Σ_k comb_filter(x, combs[k], comb_gains[k], feedback=True)) / K`, summed in list
    order, then divided once.
  - `w` passes through `allpass_comb(·, d, allpass_gain)` for each `d` of `allpasses` in order.
  - `y = (1 − mix)·x + mix·w`, the dry/wet blend of the other effects.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `combs`: 1 to 64 delays, each at least 1. `comb_gains`: one per comb, each with
    `|g| < 1`.
  - `allpasses`: 0 to 64 delays, each at least 1. `|allpass_gain| < 1`.
  - `mix` in [0, 1].
  - No default delays are built in. Schroeder's own values, such as combs of 29.7 to 43.7 ms
    and all-passes of 5 and 1.7 ms, are converted to samples by the caller.

## Consequences

- **Vectors.**
  - Expected values come from the ADR 0237 and ADR 0240 recurrences in exact rationals, rounded
    once, then the blend in stdlib floats.
  - The tolerance is `abs 1e-14, rel 1e-12`.
