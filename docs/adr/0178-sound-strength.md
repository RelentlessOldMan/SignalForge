# ADR 0178: Sound strength

Status: accepted, 2026-11-16. It goes with the ISO 3382 parameters in ADRs 0171 to 0177.

## Context

ISO 3382-1 gives the sound strength as `G = 10·log10(Σ h² / Σ h_10²)`. Here `h_10` is the same
source's response measured in a free field at 10 m. Implementations differ on three points:

- whether the two responses must share a length and sample rate;
- what a silent response gives;
- whether the early and late forms (G80, G_late) are built in.

## Decision

- **The API.** In `measurements`:
  - Python: `sound_strength(impulse_response, reference)`.
  - C#: `Measurements.SoundStrength(impulseResponse, reference)`.
  - The result is in dB.
  - Both responses are real, or both complex (the C# overloads), and use `|h|²`.
- **No sample rate.** The result is a ratio of plain sums, so the lengths may differ and there
  is no sample-rate argument. Both responses must be sampled at the same rate, which is the
  caller's job, as is the reference's calibration to 10 m.
- **The windows.** G80 and G_late are the caller's slices of `impulse_response`, using the
  boundary rule of ADR 0172. They need no argument here.
- **Zeros.**
  - A response with no energy gives `−inf`.
  - A reference with no energy is `invalid_argument`.
- **The rules.**
  - Both responses are one-dimensional, finite and not empty.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors are exact hand sums.** They are worked in fractions, with the logarithm in 50-digit
  `decimal`. The cases are:
  - unequal lengths;
  - a 10 m free-field reference against itself, which gives 0 dB;
  - a doubled amplitude, which gives `20 log10 2`;
  - complex input;
  - a silent response, which gives `−inf`;
  - the errors.
