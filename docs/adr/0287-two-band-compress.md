# ADR 0287: Two-band compressor

Status: accepted, 2026-11-17.

## Context

A single compressor turns the whole signal down when any part of it is loud, so a loud bass note
also pumps the treble. A multiband compressor splits the signal and compresses each band on its
own. ADR 0285 gives the split; this compresses the two bands and sums them.

## Decision

- **The API.**
  - Python: `two_band_compress(samples, order, cutoff, sample_rate, low_threshold_db, low_ratio,
    high_threshold_db, high_ratio, attack, release)` in `dsp`.
  - C#: `Dsp.TwoBandCompress(samples, order, cutoff, sampleRate, lowThresholdDb, lowRatio,
    highThresholdDb, highRatio, attack, release)`.
  - Flat arguments rather than a settings object, so the vectors and the two languages bind
    them the same way. The bands share the attack and release.
  - Real samples only.
- **The value.**
  - `b = crossover_split(samples, order, cutoff, fs)`.
  - The output is `compress(b.low, low_threshold_db, low_ratio, attack, release) +
    compress(b.high, high_threshold_db, high_ratio, attack, release)`: hard knee, no make-up.
  - With both ratios 1 the output is the crossover's all-pass of the input.
- **The rules.**
  - The splitter's rules for `samples`, `order`, `cutoff` and `fs`.
  - The compressor's rules for each threshold, each ratio, `attack` and `release`.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The bands are the stdlib Butterworth
    sections of ADR 0285's generator run in exact rationals; each band's envelope is exact
    rationals and its level, gain and factor are floats, as in ADR 0257's generator.
  - The tolerance is `abs 1e-14, rel 1e-11`.
- More bands, or per-band attack, release, knee and make-up, would be a new function.
