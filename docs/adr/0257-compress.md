# ADR 0257: Feed-forward compressor

Status: accepted, 2026-11-17.

## Context

ADR 0238 gives a peak detector, and ADR 0254 gives the static curve of a compressor in dB. A
compressor joins them: it follows the level, turns it into a gain and applies the gain to the
signal. This ADR fixes how they are joined, so both languages give the same samples.

## Decision

- **The API.**
  - Python: `compress(samples, threshold_db, ratio, attack, release, *, knee_db=0.0,
    makeup_db=0.0)` in `dsp`.
  - C#: `Dsp.Compress(samples, thresholdDb, ratio, attack, release, kneeDb = 0, makeupDb = 0)`.
  - Real or complex in, the same kind out.
- **The value.** For each sample `n`:
  - `e[n]` is the envelope follower of ADR 0238 with `attack` and `release`.
  - If `e[n] > 0`, then `L[n] = 20·log10(e[n])`, and `g[n]` is the compressor gain of ADR 0254
    at `L[n]`.
  - If `e[n] = 0`, the level is −∞ dB, below every threshold, so `g[n] = 0`.
  - `y[n] = x[n] · 10^((g[n] + makeup_db)/20)`. The factor is real, so a complex sample keeps its
    phase.
  - The detector smooths the level, not the gain. It is a feed-forward design with no look-ahead.
- **The rules.**
  - `threshold_db` and `makeup_db` must be finite.
  - `ratio` must be finite and `≥ 1`.
  - `knee_db` must be finite and `≥ 0`.
  - `attack` and `release` must be finite, in `[0, 1)`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The generator runs the envelope in exact rationals and the rest in stdlib floats, from the
    definitions in ADRs 0238 and 0254.
  - It checks the instant cases, where `attack = release = 0`, against the closed form
    `|y| = 10^(T/20)·(|x|/10^(T/20))^(1/ratio)` above the threshold.
  - `log10` and the power may differ by an ulp between the languages, so the tolerance is
    `rel 1e-12`.
