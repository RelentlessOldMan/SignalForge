# ADR 0283: Tilt EQ

Status: accepted, 2026-11-17.

## Context

A tilt equaliser turns the whole spectrum about a pivot frequency. One end goes up by half the
gain and the other goes down by half, so the level at the pivot is unchanged. It is a single
first-order section, a gentler partner to the shelves of ADR 0282.

## Decision

- **The API.**
  - Python: `tilt_eq(frequency, gain_db, sample_rate)` in `dsp`.
  - C#: `Dsp.TiltEq(frequency, gainDb, sampleRate)`.
  - Both return one section `[b0, b1, 0, 1, a1, 0]`, shape `(1, 6)`.
- **The prototype.**
  - `H(s) = (T·s + 1)/(s + T)` with `T = 10^(gain_db/40)` and `s = j` at the pivot.
  - Its gain is `1/T` at DC (`−gain_db/2` dB), `T` at infinity (`+gain_db/2` dB) and 1 at the
    pivot.
- **The coefficients.** With `t = tan((π·frequency)/fs)`, by the bilinear transform:
  - `b0 = (T + t)/(1 + T·t)`;
  - `b1 = (t − T)/(1 + T·t)`;
  - `a1 = (T·t − 1)/(1 + T·t)`.
- **The rules.**
  - `0 < frequency < fs/2`, finite.
  - `gain_db` must be finite, and `fs` finite and positive.
  - `gain_db = 0` gives `[1, 0, 0, 1, 0, 0]` up to rounding.

## Consequences

- **Vectors.**
  - Expected values come from the bilinear transform done in exact rationals at the float `t`
    and `T`.
  - The generator checks the DC and fs/2 gains, `1/T` and `T`, exactly.
  - The tolerance is `abs 1e-14, rel 1e-13`.
