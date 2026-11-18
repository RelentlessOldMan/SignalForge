# ADR 0255: Noise gate

Status: accepted, 2026-11-17.

## Context

A noise gate mutes a signal when it is quiet, so background noise between words or notes does
not pass. A hold time keeps the gate open for a short while after the signal drops. Without it,
the gate would chop a decaying tail or the quiet points of a waveform near its zero crossings.

## Decision

- **The API.**
  - Python: `noise_gate(samples, threshold, *, hold=0)` in `dsp`.
  - C#: `Dsp.NoiseGate(samples, threshold, hold = 0)`.
  - Real or complex in, the same kind out.
- **The value.**
  - A counter `c` starts at `hold + 1`, so the gate starts closed.
  - For each sample:
    - If `|x[n]| > threshold`, then `c = 0`.
    - Otherwise `c` goes up by 1. It stops at `hold + 1`.
    - The output is `y[n] = x[n]` if `c ≤ hold`, else `0`.
  - The comparison is strict, so a sample exactly at the threshold does not open the gate.
  - With `hold = 0`, the gate passes exactly the samples above the threshold.
  - `|x|` is `np.abs` for complex input, and `Complex.Abs` in C#.
  - The gate switches hard. Smoothing the gain is left to an envelope follower (ADR 0238).
- **The rules.**
  - `threshold` must be finite and `≥ 0`.
  - `hold` must be an integer `≥ 0`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values are exact, since each output is either the input sample or 0. They come
    from the counter definition, run by hand.
  - Complex cases use 3-4-5 magnitudes.
  - The cases include samples exactly at the threshold, and a hold that bridges a gap or expires
    inside one.
