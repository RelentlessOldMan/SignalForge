# ADR 0154: Mel scale

Status: accepted, 2026-11-16.

## Context

The mel scale maps frequency to perceived pitch. It is the axis of mel filterbanks and MFCCs.
Two definitions are in wide use and give different numbers:

- **HTK:** `2595·log10(1 + f/700)`, smooth everywhere.
- **Slaney** (the Auditory Toolbox): linear at `200/3` Hz per mel up to 1 kHz, which is 15 mel,
  and logarithmic above, with 27 mel per factor of 6.4.

A filterbank built on one does not match a filterbank built on the other. So the choice has to
be explicit.

## Decision

- **The API.**
  - Python, in `units`: `hz_to_mel(hz, *, scale="htk")` and `mel_to_hz(mel, *, scale="htk")`.
    They are elementwise, like the other conversions, and a scalar in gives a float out.
    `scale` is `"htk"` or `"slaney"`.
  - C#: `Units.HzToMel(double hz, MelScale scale = MelScale.Htk)` and `Units.MelToHz`, with the
    enum `MelScale { Htk, Slaney }`.
- **HTK.**
  - `m = 2595·log10(1 + f/700)`.
  - The inverse is `f = 700·(10^(m/2595) − 1)`.
- **Slaney.**
  - `f_sp = 200/3`.
  - Below 1000 Hz, `m = f / f_sp`.
  - From 1000 Hz up, `m = 15 + ln(f/1000) / (ln 6.4 / 27)`.
  - The inverse is `f = f_sp·m` below 15 mel, and `1000·exp((m − 15)·ln 6.4/27)` from 15 up.
  - The branches meet at 1000 Hz and 15 mel.
- **The domain.** Frequencies and mels are finite and `≥ 0`. A negative, NaN or infinite value is
  `invalid_argument`, and so is an unknown scale.

## Consequences

- **Vectors are exact points.**
  - HTK: `0 ↦ 0`, `6300 ↦ 2595` (`1 + 9 = 10`), `69300 ↦ 5190`, and the inverses. `700 ↦
    2595·log10 2` is computed in 50-digit `decimal`.
  - Slaney: `500 ↦ 7.5`, `1000 ↦ 15`, `6400 ↦ 42`, and the inverses. `2000 ↦ 15 + 27·ln 2/ln 6.4`
    is computed in `decimal`.
  - The errors.
- **Tests.**
  - The two functions are inverses on a grid in both scales.
  - Both scales are increasing.
  - Python maps arrays elementwise.
- **Later.** A mel filterbank, then MFCCs, can take `scale` and pass it through.
