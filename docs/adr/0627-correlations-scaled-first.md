# ADR 0627: Correlations divided by each record's largest magnitude first

Status: accepted, 2026-11-26. Amends ADRs 0371–0373.

## Context

The Pearson correlation, distance correlation and biweight midcorrelation do not depend on
the scale of either record, but each forms squares or products of deviations. For values
near 1e200 those overflow, and near 1e-200 they underflow to 0. A probe on records times
1e200 gave NaN or 0 in both languages. Times 1e-200, Python raised `ZeroDivisionError`
instead of `ValueError`, and C# gave NaN.

## Decision

Once the values are checked, each record is divided by its largest magnitude, when that is
positive, before any deviation is formed. The quotients lie in [−1, 1], so the deviations
lie within ±2 and the sums of their squares within the record length. Python's
`_by_largest_magnitude` and C#'s `ScaledToLargestMagnitude` do this. The C# helper returns
the values unchanged when the largest magnitude is 0 or infinite, so the existing checks
refuse them as before.

## Consequences

- Results can differ from the old ones in the last bits. Every existing vector still passes
  in both languages, within its tolerance.
- Each generator gained `huge` and `tiny` cases: a hand-checked case with both records times
  2^1000 or 2^−1000. A power of 2 scales every value exactly, and the measures are
  scale-free, so the expected value is the base case's. All 6 failed in both languages before
  the change. Mutation checks: dividing by `min(top, 1)` failed the 3 `huge` cases, and by
  `max(top, 1)` the 3 `tiny` cases, in each language.
- A wider probe, which multiplies every scale-free function's arguments by 1e±200 and
  1e±300, found more of the same: Cohen's d, Hedges' g, Glass's delta, the Buishand range,
  the SNHT, the von Neumann ratio, time irreversibility, the energy-time curve, the
  Schroeder and noise-compensated decays, and the sound strength. `docs/status.md` lists
  them as a lead.
