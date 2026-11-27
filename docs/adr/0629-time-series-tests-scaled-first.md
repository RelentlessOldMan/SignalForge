# ADR 0629: Scale-free time-series statistics scale the record by a power of 2 first

Status: accepted, 2026-11-26. Amends ADRs 0357, 0362, 0367 and 0368.

## Context

The time irreversibility, the von Neumann ratio, the Buishand range test and the standard
normal homogeneity test do not change when the record is multiplied by a positive number,
but each forms squares of deviations or of increments. With values near 1e200 those
overflow, and the results came out as 0 or NaN. Near 1e-200 they underflow to 0, and the
statistics refused the record as constant. This happened in both languages.

## Decision

Once the samples are checked, or, in C#, before the loop that checks them, the record is
scaled by the power of 2 that brings its largest magnitude into [1, 2), when that is
positive and finite. A power of 2 scales every value exactly, as in ADR 0628, so results
that did not overflow or underflow before are unchanged, bit for bit. Python uses
`_by_power_of_2` (`np.ldexp`). C# `ScaledByPowerOf2` uses `Math.ScaleB`, and leaves a record
with an infinite or NaN value unchanged, so the existing finiteness check refuses it as
before.

## Consequences

- Each generator gained `huge` and `tiny` cases: a hand-checked case times 2^1000 or
  2^−1000, with the base case's expected value, since the statistic is scale-free and the
  scaling is exact. All 8 failed in both languages before the change. Mutation checks:
  scaling by 2^−min(e, 0) failed the 4 `huge` cases, and by 2^−max(e, 0) the 4 `tiny`
  cases, in each language.
