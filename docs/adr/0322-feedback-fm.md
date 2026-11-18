# ADR 0322: Feedback FM operator

Status: accepted, 2026-11-18.

## Context

An FM operator that modulates its own phase with its last output turns a sine into a bright
wave close to a sawtooth as the feedback rises. One operator and one multiply give a
continuous brightness control, which is why FM synthesizers put feedback on one operator. It
complements the two-operator FM tone (ADR 0306).

## Decision

- **The API.**
  - Python: `feedback_fm(sample_rate, num_samples, frequency, feedback, amplitude=1, phase=0)`
    in `waveforms`.
  - C#: `Waveforms.FeedbackFm`, same arguments.
  - Real output, `phase` in cycles.
- **The value.**
  - `u[n]` is the oscillators' phase. `β = feedback`.
  - `s[−1] = 0` and `s[n] = sin((2π·u[n]) + (β·s[n−1]))`, computed in that order. Then
    `y = A·s`.
  - The feedback uses the unscaled `s`, so the shape does not depend on `amplitude`.
  - `β = 0` gives the sine `A·sin(2π·u)`.
- **The rules.**
  - `sample_rate` positive and finite. `num_samples` an integer of at least 0.
  - `frequency`, `amplitude` and `phase` finite.
  - `feedback` finite with `0 ≤ feedback ≤ 1.5`. Near 1.5 the wave is close to a sawtooth.
    Above that the one-sample loop starts to oscillate on its own and the tone turns rough
    and noisy.

## Consequences

- **Vectors.**
  - `u` comes from exact rationals and is rounded once. The generator runs the recursion with
    `math.sin`.
  - Each step multiplies an error in `s[n−1]` by `β·cos(·)`, at most `β`. Libraries' `sin`
    differ by an ulp at most, so the cases are at most 48 samples long.
  - The tolerance is `abs 1e-11, rel 1e-11`.
