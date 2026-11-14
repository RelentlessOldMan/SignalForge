# ADR 0069: Decision-feedback equalizer

Status: accepted, 2026-11-13

## Context

A linear equalizer (ADR 0066) inverts the channel's spectrum, so where the channel has a deep
notch it amplifies the noise there. A decision-feedback equalizer (DFE) removes the interference
that past symbols leave on the current one by subtracting it, using symbols already decided, so
the forward filter no longer has to invert that part and enhances less noise. The choices are the
API shape, the sign of the feedback, how the two filters adapt, and what feeds the feedback
before there are decisions.

## Decision

- A separate block in `sync`: `dfe_equalizer(samples, training, num_taps, num_feedback, step, *,
  samples_per_symbol=1, center=None, decision=None)` (C# `Sync.DfeEqualizer`), returning
  `DfeEqualization(symbols, errors, taps, feedback_taps)`. `lms_equalizer` and `Equalization` stay
  as they are; the two share one implementation, and `num_feedback = 0` gives exactly
  `lms_equalizer`'s results.
- The forward part is the LMS equalizer's, unchanged. The feedback taps `b_j` (`j = 1 … M`) act
  on the past references `d_{n−j}` (training symbols, then decisions; 0 before the first) and are
  **added**: `y_n = Σ w_i·u_i + Σ b_j·d_{n−j}`, so they converge to minus the post-cursor
  interference. One sign everywhere and no special case in the update.
- **One normalized LMS update** over the joined regressor `[u, d_past]`: its power is both parts'
  power, and both filters move with the same `μ/P`. The feedback taps start at 0.
- The feedback needs a reference for every output: with `M ≥ 1`, either `decision` is given or the
  training covers every output. A held filter with decisions it cannot make has no meaning.

## Consequences

- Wrong decisions feed back (error propagation): a burst of errors can follow one. That is the
  DFE's nature, not a defect to hide; tests measure it at a working SNR.
- No tentative decisions, no delayed-decision tree search, no RLS.
- A link option comes in a later slice, with its own BER bound question.
