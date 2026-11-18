# ADR 0280: Auto-wah

Status: accepted, 2026-11-17.

## Context

An auto-wah, or envelope filter, is a resonant band-pass whose centre follows the input's
level. Louder notes open the filter upward. It joins two pieces already here: the envelope
follower (ADR 0238) and the state-variable filter (ADR 0279). The trapezoidal SVF keeps its
state meaningful while the cutoff changes from sample to sample.

## Decision

- **The API.**
  - Python: `auto_wah(samples, low, high, q, attack, release, sample_rate, mix)` in `dsp`.
  - C#: `Dsp.AutoWah(samples, low, high, q, attack, release, sampleRate, mix)`.
  - Real and complex; the output is the same kind.
- **The sweep.**
  - `e = envelope_follower(samples, attack, release)`, which follows `|x|`.
  - `fc[n] = low + (high − low)·min(e[n], 1)`.
  - `g[n] = tan((π·fc[n])/fs)`.
- **The filter.**
  - It is the SVF recursion of ADR 0279 with `k = 1/q`.
  - `a1`, `a2` and `a3` are recomputed from `g[n]` at each sample, and the state carries over.
  - The wet signal is `k·v1`, the band-pass scaled to unity peak gain.
  - A complex signal runs through the filter part by part, with the one envelope.
- **The mix.** `y = x·(1 − mix) + wet·mix`, evaluated in that order; complex part by part.
- **The rules.**
  - `0 < low ≤ high < fs/2`, all finite; `low = high` is a fixed band-pass.
  - `q` and `fs` must be finite and positive, and `mix` finite and in `[0, 1]`.
  - The envelope follower's rules for `attack` and `release`.
  - The samples must be finite and at least one.
- **The SVF** now takes a coefficient per sample internally. Its public form is unchanged and
  gives the same values.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The envelope is computed in exact
    rationals, then rounded, and the SVF is run in floats.
  - The fixed case (`low = high`) is checked against `k` times the band-pass of ADR 0279's
    direct-form biquad.
  - The tolerance is `abs 1e-12, rel 1e-12`.
