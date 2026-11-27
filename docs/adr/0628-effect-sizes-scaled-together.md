# ADR 0628: Effect sizes divide both records by one common scale first

Status: accepted, 2026-11-26. Amends ADRs 0397–0399.

## Context

Cohen's d, Hedges' g and Glass's delta do not change when both records are multiplied by the
same positive number, but each forms squares of deviations. With values near 1e200 those
overflow, and the result came out as 0. Near 1e-200 they underflow to 0, and the measures
refused the records as having no spread. This happened in both languages.

## Decision

Once the values are checked, both records are scaled by the power of 2 that brings the
largest magnitude in either into [1, 2), when that is positive. Each record is not scaled on
its own, since the measures compare the two records' means on a common scale. A power of 2
is used, not the largest magnitude itself, because it scales every value exactly: results
that did not overflow before are bit for bit the same, and an existing test that compares
two results for exact equality still holds (dividing by the largest magnitude broke it in the
last bit). Python uses `math.ldexp` in `cohen_d` and `glass_delta`. C# `ScaleTogether` uses
`Math.ScaleB` in `CohenD` and `GlassDelta`, and leaves the records unchanged when the largest
magnitude is 0 or infinite, so the existing checks refuse them as before. Hedges' g goes through Cohen's d.

## Consequences

- Results that did not overflow or underflow before are unchanged, bit for bit.
- Each generator gained `huge` and `tiny` cases: a hand-checked case with both records times
  2^1000 or 2^−1000. A power of 2 scales every value exactly, and these measures are
  unchanged by a common scale, so the expected value is the base case's. All 6 failed in
  both languages before the change. Mutation checks: scaling by 2^−min(e, 0) failed the 3
  `huge` cases, and by 2^−max(e, 0) the 3 `tiny` cases, in each language.
