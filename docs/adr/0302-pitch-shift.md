# ADR 0302: Delay-line pitch shifter

Status: accepted, 2026-11-17.

## Context

The oldest digital pitch shifter, used in the first harmonizers, reads a delay line through a
tap whose delay ramps steadily. A delay that shrinks by `ratio − 1` samples per sample reads
the input `ratio` times as fast, which raises the pitch by that ratio. The delay cannot shrink
for ever, so it wraps every window, and a second tap half a window apart is faded in while the
first one jumps. The read is the vibrato's linear interpolation (ADR 0271).

## Decision

- **The API.**
  - Python: `pitch_shift(samples, ratio, window)` in `dsp`.
  - C#: `Dsp.PitchShift(samples, ratio, window)`.
  - `window` is `W` in samples. Real samples only.
- **The value.**
  - `t = (1 − ratio)·(n/W)` and `φ = t − floor(t)`, in [0, 1).
  - `φ_b = (φ + 1/2) − floor(φ + 1/2)`.
  - Tap A has the delay `d_a = W·φ`, tap B `d_b = W·φ_b`.
  - Each tap reads `p = n − d`, `i = ⌊p⌋`, `f = p − i`, `x[i]·(1 − f) + x[i+1]·f`, with
    `x[k] = 0` outside the signal.
  - `y = sin²(πφ)·A + cos²(πφ)·B`. The gains sum to 1, and each tap's gain is 0 where its
    delay wraps.
  - At `ratio = 1`, `φ` stays 0, and the output is the input delayed by `W/2`.
  - The crossfade modulates the output at the window rate `|1 − ratio|·fs/W`. A longer window
    lowers that rate but smears transients more.
- **The rules.**
  - The samples must be real, finite and at least one.
  - `ratio` finite and positive.
  - `window` finite and at least 1.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription of the rule. Dyadic ratios and windows
    keep the phase exact. One case is non-dyadic.
  - The tolerance is `abs 1e-12, rel 1e-12`.
