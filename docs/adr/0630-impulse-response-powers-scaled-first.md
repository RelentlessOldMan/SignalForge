# ADR 0630: Room-acoustic measures square the impulse response at a power-of-2 scale

Status: accepted, 2026-11-26. Amends ADRs 0171–0173, 0176, 0178, 0179, 0181, 0183 and 0186.

## Context

The room-acoustic measures are ratios of energies: the Schroeder decay, the reverberation and
early decay times read from it, the noise-compensated decay, the energy-time curve, clarity,
definition, the centre time, the modulation transfer function, stage support and the sound
strength. None of them changes when the impulse response is multiplied by a positive number,
or, for the sound strength, when the response and its reference are multiplied by the same
number. But each squares the samples. With values near 1e200 the squares overflow and the
results came out as NaN or wrong. Near 1e-200 they underflow to 0, and the measures refused
the response as all zero or as having no energy above the noise. This happened in both
languages, for all 11. A probe of the 1- and 2-argument functions had found 4 of them; the
rest take a sample rate as well and were not probed.

Refusing was wrong: an impulse response is in arbitrary units, and a tiny one is still a
response.

## Decision

The samples are squared after scaling them by the power of 2 that brings the largest real or
imaginary magnitude into [1, 2), when that is positive and finite. A power of 2 scales every
value exactly, as in ADRs 0628 and 0629, so results that did not overflow or underflow
before are unchanged, bit for bit. The sound strength uses one exponent for the response and
its reference, from the largest magnitude in either, since its value is the ratio of their
energies. The energy-time curve scales the analytic signal, whose squares it forms.

Python's `_powers` and `_shared_exponent` do this for every measure. In C#, `ResponsePowers`
takes the exponent from `LargestMagnitude` and `PowerOf2Exponent`, and so do
`SchroederDecay`, `EnergyTimeCurve` and the sound strength's reference. A record with an
infinite or NaN value is left unscaled, so the existing finiteness checks refuse it as
before.

## Consequences

- Limitation: a sound strength whose response and reference differ in scale by more than
  about 2^540 still underflows the smaller of the two energies, since they share one
  scale. Not handled.
- Each generator gained `huge` and `tiny` cases: hand-checked or exactly computed cases,
  real and complex, times 2^1000 or 2^−1000 (2^−960 for two cases whose smallest values
  would otherwise become subnormal), with the base case's expected value, since the measures
  are scale-free and the scaling is exact. All 36 failed in both languages before the
  change. Mutation checks: capping the exponent at 0 from above failed the 18 `huge` cases,
  and from below the 18 `tiny` cases, in each language.
