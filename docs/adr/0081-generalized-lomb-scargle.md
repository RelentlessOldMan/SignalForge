# ADR 0081: Generalized Lomb-Scargle periodogram

Status: accepted, 2026-11-13

## Context

The classic Lomb-Scargle periodogram (ADR 0059) fits `a cos ωt + b sin ωt` to the values after
subtracting their mean. On uneven times the sample mean is not the signal's mean: a sinusoid
sampled more near its peaks than its troughs moves the sample mean, and the fit then misses
power. Measurements also often carry an uncertainty per sample. Zechmeister & Kürster (2009)
fit `a cos ωt + b sin ωt + c` with weights `1/σ²`, so the mean floats at each frequency. ADR 0059
left this for a separate function.

## Decision

- `generalized_lomb_scargle(times, values, frequencies, *, uncertainties=None,
  normalization="standard")`. In C#, `Spectral.GeneralizedLombScargle(times, values, frequencies,
  uncertainties = null, normalization = Standard)`, with the existing `LombScargleNormalization`.
  `uncertainties` are the σₙ, finite and `> 0`, one per sample. None means every σ is 1. There
  is no `center`, because the floating constant does that job.
- With `W = Σ 1/σₙ²` and the weights `wₙ = (1/σₙ²)/W` (which sum to 1), every sum below is
  weighted and centered: `Ȳ = Σ wy`, `YY = Σ wy² − Ȳ²`, and the same for any pair of `y`,
  `cos ω(t − τ)` and `sin ω(t − τ)`.
- `τ` is Zechmeister & Kürster's offset, `atan2(2·CS, CC − SS)/(2ω)`, from the centered sums at
  τ = 0. After the offset the centered cross term is 0, so
  `p = (YC²/CC + YS²/SS)/YY`. As in ADR 0059, a term whose denominator `CC` or `SS` is below
  `1e-12` is 0. The threshold has no `N`, because the weights sum to 1.
- `"standard"` returns `p`, which is `(χ²₀ − χ²)/χ²₀`: the fraction of the weighted scatter about
  the weighted mean that the fit explains, between 0 and 1. It needs `YY > 0`. `"power"`
  returns `½·W·YY·p = ½(χ²₀ − χ²)`, which needs no `YY > 0`. With unit σ this is Scargle's `P` on
  the same scale as ADR 0059's power.
- On even samples with `f` at a bin, the cosine and sine sum to 0, so with unit σ the result
  equals the classic centered one.

## Not now

The false-alarm probability for the generalized form. The ADR 0062 formula with `d = 3` holds
here exactly, because the constant is fitted at each frequency, but it is not wired up.
Uncertainties for the classic function are also left out.

## Consequences

Expected values come from a stdlib generator that solves the weighted 3×3 normal equations for
`a cos ωt + b sin ωt + c` at each frequency, with no τ. It gives `χ²` directly, and
`p = (χ²₀ − χ²)/χ²₀`. By-hand cases:

- `3 + cos 2πt` at five times `0, ¼, …, 1` fits exactly: standard 1, power `½Σ(y − ȳ)² = 1.4`.
  With the last σ ½, the power is 2.0.
- Even samples at Nyquist (`sin` drops out): `2 + (1, −1, 1, −1)` gives standard 1, power 2.
