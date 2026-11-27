# ADR 0631: Five more scale-free statistics scale the record first

Status: accepted, 2026-11-26. Amends ADRs 0341, 0343, 0344, 0358 and 0359; extends ADR 0629.

## Context

The dispersion entropy, the weighted permutation entropy, the increment entropy, the cosine
similarity entropy and the Ljung–Box statistic do not change when the record is multiplied by
a positive number. Each squares the samples or their deviations: the dispersion and increment
entropies for a standard deviation, the weighted permutation entropy for its window
variances, the cosine similarity entropy for the vector norms, and the Ljung–Box statistic for
the autocovariances. With values near 1e200 the squares overflowed and the results were NaN
or wrong. Near 1e-200 they underflowed to 0 and the functions refused the record as constant
or all zero. Both languages had this. The scale probe of ADRs 0624–0629 covered only 1- and
2-argument functions; these take an order, a threshold or a lag as well and were missed.

## Decision

As in ADR 0629, each function scales the record by the power of 2 that brings its largest
magnitude into [1, 2), when that is positive and finite, after its finiteness check and
before any other arithmetic. Python uses `_by_power_of_2` and C# `ScaledByPowerOf2`. The
scaling is exact, so results that did not overflow or underflow before are unchanged, bit
for bit. The thresholds these functions take (the cosine similarity entropy's `r`, the class
and level counts) are already scale-free, so nothing else changes.

## Consequences

- Each of the five generators gained `huge` and `tiny` cases: an existing case times 2^1000
  or 2^−1000, with the base case's expected value. All 10 failed in Python before the
  change. Mutation checks: capping the exponent at 0 from above failed all 5 `huge` cases,
  and from below all 5 `tiny` cases, in each language.
- The probe of the 3+-argument functions also found six signal-energy measures that fail
  the same way (`autocorrelation_pitch`, `iacc`, `lateral_fraction`, `temporal_centroid`,
  `power_ccdf_level` and `gcc_phat`). They are a separate lead in `docs/status.md`.
- Three other hits of that probe were false alarms: the approximate entropy, the
  distribution entropy and the recurrence quantification take an absolute radius or bin the
  distances, and agree at exact power-of-2 scales.
