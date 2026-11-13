# 0017: Zero-phase filtering

Date: 2026-11-13. Status: accepted.

## Context

Measuring a filtered signal (an envelope, a band's level over time) should not shift it in time.
Running a filter forward and then backward cancels the phase, but the edges need a rule: with zero
initial state each pass starts with a transient, and the result near the ends depends on how the
input is extended. Tools differ (padding kind, padding length, initial state), so the rule is
fixed here.

## Decision

- **Forward, then backward, over an odd extension.** The input is extended at each end by `pad`
  samples reflected about the end sample (`2·x[0] − x[i]`), which continues a slope, not just a
  level, so a smooth input stays smooth across the join.
- **Each pass starts in its steady state** for a constant equal to its first sample, section by
  section. A constant input then passes with no transient at all, and the residual transient from
  a slope is small. The state is defined by the difference equation's past inputs and outputs, so
  it does not depend on the arithmetic form.
- **Default pad `3·(2·sections + 1)`**, a few times the filter's order; `pad = 0` is allowed. The
  input must be longer than the pad, and a section with a pole at `z = 1` (no steady state) is an
  error.
- One function, not a streaming filter: running backward needs the whole input.
- Implemented from the definitions; no third-party code.

## Consequences

- Magnitude is `|H|²`: the cut-off of a Butterworth design moves to its −6 dB point, and the
  stop band attenuation doubles in dB.
- Results within a few time constants of either end still depend on `pad` and the extension; the
  vectors fix them, so a change is visible.
