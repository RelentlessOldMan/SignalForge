# ADR 0260: Ring modulator

Status: accepted, 2026-11-17.

## Context

A ring modulator multiplies a signal by a sine carrier. Each input frequency `f₀` becomes the
pair `f₀ ± f`, and the carrier itself is suppressed. It is double-sideband suppressed-carrier
modulation, and also a classic audio effect. The carrier phase is part of the definition, so
both languages must build the argument the same way as the tone (`tone`, conventions: tones).

## Decision

- **The API.**
  - Python: `ring_modulate(samples, frequency, sample_rate, *, phase=0.0)` in `dsp`.
  - C#: `Dsp.RingModulate(samples, frequency, sampleRate, phase = 0)`.
  - Real or complex in, the same kind out.
- **The value.**
  - `y[n] = x[n]·cos(2π·f·(n/fs) + φ)`, with `n` from 0.
  - The argument is built as for `tone`: `(2π·f)·(n/fs) + φ`, in that order.
  - A complex sample is scaled part by part by the real carrier.
- **The rules.**
  - `sample_rate` must be finite and `> 0`.
  - `frequency` and `phase` must be finite. Any frequency is allowed, including negative ones
    and ones above Nyquist, as for `tone`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.**
  - The expected values come from the stdlib `math.cos` on the same argument.
  - The fs/4 and fs/2 cases are checked by hand against `1, 0, −1, 0` and `±1`.
  - `cos` may differ by an ulp between the languages, so the tolerance is `abs 1e-14`.
