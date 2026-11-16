# ADR 0181: Early decay time

Status: accepted, 2026-11-16. It goes with the reverberation time of ADR 0171.

## Context

ISO 3382-1's early decay time (EDT) is the reverberation time fitted over the first 10 dB of
the Schroeder decay, from 0 to −10 dB, and scaled to 60 dB. Listeners judge reverberance from
this early part. `reverberation_time(h, fs, start_db=0, stop_db=-10)` already computes it, but
only a caller who knows the levels can find it.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `early_decay_time(impulse_response, sample_rate)`.
  - C#: `Measurements.EarlyDecayTime(impulseResponse, sampleRate)`.
- **What it is.** It is exactly `reverberation_time` with `start_db = 0` and
  `stop_db = −10`. It has the same fit, the same threshold samples (the first sample at or
  below each level, ADR 0171) and the same errors. The fit therefore starts at sample 0, where
  the decay is 0 dB.
- **No overrides.** It takes no level arguments. A caller who wants other levels uses
  `reverberation_time`.

## Consequences

- **Vectors.** Expected values come from the exact geometric Schroeder tails of
  `h = c·rⁿ`, including a sum of two decays where EDT and T20 differ, with the least-squares
  slope worked in 50-digit `decimal`. Every curve value is kept at least `1e−6` dB away from
  −10 dB.
