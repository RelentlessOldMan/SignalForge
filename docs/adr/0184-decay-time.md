# ADR 0184: Decay time from a curve

Status: accepted, 2026-11-16. It goes with ADR 0171 (reverberation time) and ADR 0183
(noise-compensated decay).

## Context

`reverberation_time` always fits the plain Schroeder decay of the response. A noise-compensated
decay (ADR 0183), or a curve the caller has corrected some other way, needs the same fit without
the integration step.

## Decision

- **The API.** In `measurements`:
  - Python: `decay_time(decay, sample_rate, *, start_db=-5.0, stop_db=-25.0)`.
  - C#: `Measurements.DecayTime(decay, sampleRate, startDb = -5, stopDb = -25)`.
  - `decay` is a real dB curve, one value per sample.
- **The fit.** It is exactly the fit of ADR 0171:
  - `n1` is the first sample at or below `start_db`, and `n2` the first at or below `stop_db`;
  - the least-squares slope `m` (dB/s) is taken over `n1 ≤ n < n2`;
  - the result is `−60/m`.

  `reverberation_time(h, fs, …)` is `decay_time(schroeder_decay(h), fs, …)`. Python computes it
  through `decay_time`, and C# goes through the same private fit.
- **The curve.**
  - It need not start at 0 dB or be monotonic.
  - `−inf` is allowed: it counts as below every level, so it can only stand at or after `n2`
    and never inside the fit.
  - NaN and `+inf` are `invalid_argument`.
  - The curve must be one-dimensional and not empty.
- **The errors** are those of `reverberation_time`:
  - `stop_db < start_db ≤ 0`, both finite;
  - the curve must reach `stop_db`;
  - at least two samples must lie in the fit;
  - the slope must be negative;
  - `sample_rate` must be finite and positive.

## Consequences

- **Vectors.**
  - Straight lines give `−60/slope` exactly.
  - A hand-made five-point curve gets its least-squares slope worked in fractions.
  - A curve ending in `−inf`, and a rising curve that gives a positive slope (an error), are
    included.
