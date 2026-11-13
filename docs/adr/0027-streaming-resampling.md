# ADR 0027: Streaming resampling

Status: accepted, 2026-11-13

## Context

`resample` works on a whole signal and removes the filter's delay by looking ahead `(N − 1)/2`
samples at the up-sampled rate. A stream cannot look ahead, so a stateful resampler has to choose
when each output comes out and how its timing relates to `resample`.

## Decision

- **`Resampler(up, down, taps=None)` with `process(chunk)` and `reset()`**, like `FirFilter`: the
  same real-or-complex rule, the same empty-chunk rule.
- **Causal, every output as early as possible**: `z[m] = L·Σ h[k]·u[m·M − k]` comes out with the
  chunk holding input `⌊m·M/L⌋`, its last input. After `n` inputs there are exactly `⌈n·L/M⌉`
  outputs, the count `resample` gives for `n` inputs, whatever the split.
- **Defined through `resample`**: the stream equals `resample(x, up, down, [0]·(N − 1) + h)`.
  That is the same zero-stuffed convolution, delayed by the taps' full length rather than
  centred, so it needs no new arithmetic. It also gives an exact identity for tests and vectors:
  the delayed taps have odd length `2N − 1` whatever `N` is, so the streaming taps need not be
  odd.
- The default taps are `resample`'s (`resample_taps`), or a copy when `L = M = 1`.
- The implementation is polyphase: each output sums `⌈N/L⌉` products, keeping
  `⌈N/L⌉ − 1` past inputs.

## Consequences

- The delay is the taps' full length, `N − 1` samples at the up-sampled rate; for the default
  linear-phase taps the signal itself is delayed by half that. A caller who wants `resample`'s
  alignment drops the first outputs and flushes with zeros.
- No flush method: feeding zeros does that, and its length is the caller's choice.
