# ADR 0099: Baluev false-alarm level

Status: accepted, 2026-11-15. Extends [ADR 0098](0098-lomb-scargle-baluev.md), as
[ADR 0082](0082-lomb-scargle-false-alarm-level.md) extends ADR 0062.

## Context

A detection threshold for a periodogram search is the standard value that noise exceeds with a
chosen chance, such as 1%, anywhere up to `f_max`. The Baluev estimate (ADR 0098) has no closed-form
inverse, because `z` appears both in `P₁` and in `τ`.

## Decision

- Python `lomb_scargle_false_alarm_level_baluev(probability, times, max_frequency, *,
  center=True)`. C# `Spectral.LombScargleFalseAlarmLevelBaluev(probability, times, maxFrequency,
  center = true)`. The arguments are those of the forward function, with `probability` in `[0, 1]`
  in place of `power`.
- The level is found by bisection on `[0, 1]`. Write `F(z)` for the forward value, so `F(0) = 1`.
  Start from `lo = 0` and `hi = 1`, and repeat:
  - Take `m = lo + (hi − lo)/2`.
  - Stop if `m` equals `lo` or `hi`, because the interval cannot shrink further.
  - If `F(m) > p`, set `lo = m`; otherwise set `hi = m`.

  The result is `hi`, the smallest `z` found with `F(z) ≤ p`. The loop takes at most about 1075
  steps (down to the smallest subnormal). Every step is the same comparison in both languages, so
  they differ only where their `F` differs in the last bit at a step's `m`.
- `F` is not quite monotone, and the result is defined as the crossing bisection finds.
  - Near `z = 0`, where `F` is above about 0.998, `F` can rise by up to about `2·10⁻⁵`. That
    matters only for `p` that close to 1, where the estimate means little anyway.
  - With `N = d + 1`, `(1 − z)^0 = 1` keeps `τ` positive, so `F(1)` is above 0 and `F` is not
    monotone. Any `p` below what bisection meets then gives 1.
  - `p = 0` gives 1. `p = 1` gives 0, returned directly, because bisection would otherwise close on
    the smallest subnormal.
- The errors are those of the forward function, with `p` outside `[0, 1]` or NaN in place of `z`.

## Consequences

- The expected values are round trips. The generator computes `p = F(z)` for a chosen `z` with
  its own `math.lgamma` route, and the expected level is that `z`. The tolerance is relative
  `1e-9`, because the root inherits the slope of `F`. Round trips avoid `N = d + 1`, where one
  can miss. The ends and an `N = 4` case worked by hand are written out.
