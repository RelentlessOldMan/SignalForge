# ADR 0274: Phaser

Status: accepted, 2026-11-17.

## Context

A phaser passes a signal through a chain of first-order allpasses and adds the result to the dry
signal. Each allpass turns the phase by `−π/2` at its break frequency. Where the chain's total
phase reaches an odd multiple of `−π`, the wet path cancels the dry one and the sum has a notch.
An oscillator sweeps the break frequency, so the notches move. Unlike a flanger's comb, the
notches are not evenly spaced in frequency.

## Decision

- **The API.**
  - Python: `phaser(samples, stages, low, high, rate, sample_rate, mix)` in `dsp`.
  - C#: `Dsp.Phaser(samples, stages, low, high, rate, sampleRate, mix)`.
  - Real and complex; the output is the same kind.
- **The sweep.**
  - `fc[n] = low + (high − low)·((1 − cos((2π·rate)·(n/fs)))/2)`, so it starts at `low`.
  - `t[n] = tan((π·fc[n])/fs)` and `c[n] = (t[n] − 1)/(t[n] + 1)`: the first-order allpass
    coefficient of ADR 0033 at `fc[n]`.
- **The chain.**
  - Each stage is `y[n] = c[n]·x[n] + x[n−1] − c[n]·y[n−1]`, from rest (`x[−1] = y[−1] = 0`).
  - `stages` such stages run in series, all with the same `c[n]`.
  - A complex signal runs through the chain part by part.
- **The mix.** `y = x·(1 − mix) + w·mix`, with `w` the chain's output, evaluated in that order;
  complex part by part.
- **The rules.**
  - `stages` must be an integer `≥ 1`.
  - `0 < low ≤ high < fs/2`, all finite; `low = high` gives a fixed allpass chain.
  - `rate` must be finite, `fs` finite and positive, `mix` finite and in `[0, 1]`.
  - The samples must be finite and at least one.
- **No feedback.** A feedback phaser feeds the chain's output back to its input; it would be its
  own slice.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription with `math.cos` and `math.tan`.
  - A fixed chain at `fs/4` has `c ≈ 0`, so each stage is close to a one-sample delay; the
    generator checks this against the shifted input.
  - The tolerance is `abs 1e-12, rel 1e-12`. The recursion carries any last-bit difference in
    `cos` or `tan` between the languages, but `|c| < 1`, so it fades.
