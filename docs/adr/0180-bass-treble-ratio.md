# ADR 0180: Bass and treble ratio

Status: accepted, 2026-11-16. It goes with the room-acoustic parameters in ADRs 0171 to 0179.

## Context

Beranek's bass ratio and treble ratio compare the reverberation time at low and high
frequencies with its mid-frequency value:

- `BR = (T125 + T250) / (T500 + T1000)`;
- `TR = (T2000 + T4000) / (T500 + T1000)`.

Implementations differ in how the band times are passed in, and in what they accept.

## Decision

- **The API.** In `measurements`:
  - Python: `bass_ratio(times)` and `treble_ratio(times)`.
  - C#: `Measurements.BassRatio(times)` and `Measurements.TrebleRatio(times)`.
- **The input.** `times` holds exactly six octave-band reverberation times, in seconds, in the
  order 125, 250, 500, 1000, 2000, 4000 Hz. One shape serves both ratios, and it is what a loop
  over `reverberation_time` on octave-band filtered responses gives. Bands the ratio doesn't
  use must still be valid.
- **The rules.**
  - The times are one-dimensional, exactly six long, finite and positive.
  - Anything else is `invalid_argument`.
  - The result is a plain ratio, not in dB.

## Consequences

- **The caller's job.** The band filtering and each band's `reverberation_time` stay with the
  caller.
- **Vectors are exact fractions.**
