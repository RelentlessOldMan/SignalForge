# ADR 0098: Baluev false-alarm probability for a Lomb-Scargle search

Status: accepted, 2026-11-15. Extends [ADR 0062](0062-lomb-scargle-significance.md).

## Context

`lomb_scargle_false_alarm` (ADR 0062) needs the number of independent frequencies `M`, and for a
dense grid nobody knows it: `M ≈ f_max·T` is a guess, and the grid's frequencies are correlated.
Baluev (2008, MNRAS 385, 1279) bounds the chance that noise exceeds `z` anywhere below `f_max`
using the times themselves, through an upcrossing count (the Davies bound), and gives an
"alias-free" approximation that is close to the true value for small probabilities. It is the
estimate most tools offer for a periodogram search.

## Decision

- `lomb_scargle_false_alarm_baluev(power, times, max_frequency, *, center=True)`; C#
  `Spectral.LombScargleFalseAlarmBaluev(power, times, maxFrequency, center = true)`. It takes the
  standard normalization only, like the ADR 0062 function, and `center=True` also covers the
  generalized form.
- With `N` samples, `d = 3` centered and `2` not, and `h = 1` centered and `0` not:
  `N_K = N − d` and `N_H = N − h`.
  - The one-frequency chance is `P₁ = (1 − z)^(N_K/2)`, as in ADR 0062.
  - `D = (1/N)·Σ(tₙ − t̄)²` is the variance of the times, and `W = f_max·√(4π·D)`.
  - `γ = √(2/N_H)·Γ(N_H/2)/Γ((N_H − 1)/2)`.
  - The expected number of upcrossings is `τ = W·γ·(1 − z)^((N_K − 1)/2)·√(N_H·z/2)`.
  - The value is `1 − (1 − P₁)·e^(−τ)`, computed as `−expm1(log1p(−P₁) − τ)`, so it is 1 when `P₁` is 1.
- The gamma ratio is taken from `r(n) = Γ(n/2)/Γ((n − 1)/2)`, using `r(2) = 1/√π`,
  `r(3) = √π/2` and `r(n + 2) = r(n)·n/(n − 1)`. Every factor is exact or one rounding, so neither
  language needs a log-gamma function, and both do the same operations in the same order.
- Errors: `z` must be in `[0, 1]`, there must be at least `d + 1` times, every time finite and not
  all equal, and `f_max` must be positive and finite.

## Consequences

- This is an approximation. Its error is small when the result is small, and it can be far off
  near 1. Bootstrap estimates are still not provided.
- The expected values come from a stdlib generator that uses `math.lgamma` for the gamma ratio.
  That is a route the code does not take. `lgamma` loses about `1e-11` relative at `N = 2·10⁴`
  (a difference of two values near `10⁵`), while the recurrence stays within a few ε. So the
  generator keeps `N` small, and the unit tests check large `N` against the exact rational
  product. A hand check is `N = 4` centered: there `N_H = 3`,
  `γ = √(2/3)·√π/2` and `(1 − z)^0 = 1`.
