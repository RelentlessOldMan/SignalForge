# ADR 0632: Six signal-energy measures scale their records first

Status: accepted, 2026-11-26. Amends ADRs 0119, 0147, 0150, 0174, 0175 and 0191; extends ADRs
0629–0631.

## Context

The autocorrelation pitch, the temporal centroid, the power CCDF level, GCC-PHAT, the IACC
and the lateral energy fraction do not change when their signals are scaled: the pitch lag
and voicing ratio, an energy-weighted time, a level in dB over the mean power, a delay from
the phase alone, and normalized correlations and energy ratios. Each forms squares or
products of the samples. With values near 1e200 these overflowed and the results were NaN,
or, for GCC-PHAT, the wrong lag. Near 1e-200 they underflowed to 0, the functions refused the
signals as having no energy, and GCC-PHAT again found the wrong lag. Both languages had this.
A probe of the functions with 3 or more arguments found them (signal arguments times 2^±664
and 2^±996; rates and orders unchanged).

## Decision

Each scales by the power of 2 that brings the largest real or imaginary magnitude into
[1, 2), when that is positive and finite, after its finiteness checks and before any squares:

- The autocorrelation pitch and the temporal centroid scale their one record.
- GCC-PHAT scales `x` and `y` separately, and the IACC `left` and `right` separately: the
  phase transform and the normalized correlation ignore a scale on either signal.
- The lateral energy fraction is a ratio of the figure-of-eight and omni energies, so it
  scales both by one exponent, from the largest magnitude in either.
- The power CCDF level forms the powers of the scaled record; the level is a ratio of two of
  them.

Python uses `_by_power_of_2`, `_shared_exponent` and `_powers`, and C# `ScaledByPowerOf2`,
`LargestMagnitude` and `PowerOf2Exponent`. The scaling is exact, so results that did not
overflow or underflow before are unchanged, bit for bit.

## Consequences

- Limitation: `power_ccdf` still overflows or underflows, because it returns the mean power
  itself, which is not scale-free and is out of range when the squares are. Not handled.
- Limitation: a lateral fraction whose two channels differ in scale by more than about
  2^540 still underflows the smaller energy, as for the sound strength (ADR 0630).
- Each generator gained `huge` and `tiny` cases: an existing case times 2^1000 or 2^−1000,
  real and complex where the function takes both, with the base case's expected value. All
  16 failed in Python before the change. Mutation checks: capping the exponent at 0 from
  above failed all 8 `huge` cases, and from below all 8 `tiny` cases, in each language.
- Every probe so far used real samples only. `kay_frequency`, which takes only complex
  samples, gives NaN near 2^1000 and 0 near 2^−1000; the functions that take only complex
  samples are a lead in `docs/status.md`.
