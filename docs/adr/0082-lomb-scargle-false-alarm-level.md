# ADR 0082: Lomb-Scargle false-alarm level

Status: accepted, 2026-11-13

## Context

`lomb_scargle_false_alarm` (ADR 0062) turns a standard Lomb-Scargle value into the chance that
white noise exceeds it. A detection threshold is usually wanted the other way round: the value
that noise exceeds with chance `p`, such as 1%, to draw on a plot or to compare peaks against.
The formula inverts in closed form. The generalized form (ADR 0081) fits the constant at every
frequency, so the same formula with `d = 3` (`center=True`) is exact for it at one frequency.

## Decision

- `lomb_scargle_false_alarm_level(probability, num_samples, *, num_frequencies=1, center=True)`,
  and in C# `Spectral.LombScargleFalseAlarmLevel(probability, numSamples, numFrequencies = 1,
  center = true)`. The arguments mirror the forward function, with `probability` in `[0, 1]`
  in place of `power`.
- The value is `P₁ = −expm1(log1p(−p)/M)`, which is `1 − (1 − p)^{1/M}`, and then
  `z = −expm1(2·log(P₁)/(N − d))`, which is `1 − P₁^{2/(N − d)}`. Written with
  `log1p`/`expm1`, tiny `p` and large `M` keep full precision, as in the forward function.
- `p = 0` gives 1, the largest standard value. `p = 1` gives 0.
- Errors are as for the forward function: `p` outside `[0, 1]` or NaN, `N < d + 1`, or `M < 1`.

## Consequences

Expected values come from three sources:

- By-hand cases where the exponents are whole or halves: `N = 5` centered gives `z = 1 − P₁`,
  and `N = 7` gives `1 − √P₁`.
- Round trips through ADR 0062's exact-fraction table: the probability is the exactly computed
  false alarm of a decimal `z`, and the expected value is that `z`.
- The two ends.
