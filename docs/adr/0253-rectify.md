# ADR 0253: Rectifier

Status: accepted, 2026-11-17.

## Context

Envelope detectors, power-supply models and AM demodulators rectify a signal. A full-wave
rectifier takes `|x|`. A half-wave rectifier passes the positive part and blocks the rest.

## Decision

- **The API.**
  - Python: `rectify(samples, *, full=True)` in `dsp`.
  - C#: `Dsp.Rectify(samples, full = true)`.
  - Real samples only.
- **The value.**
  - Full wave: `y = |x|`.
  - Half wave: `y = x` if `x > 0`, else `0`.
  - Negative zero gives `+0` in both modes.
  - It is memoryless.
- **The rules.** The samples must be real, finite and non-empty.

## Consequences

- **Vectors.** The expected values are exact from the definition, compared with zero tolerance.
