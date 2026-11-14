# ADR 0062: Lomb-Scargle false-alarm probability and frequency grid

Status: accepted, 2026-11-13

## Context

A Lomb-Scargle peak ([ADR 0059](0059-lomb-scargle.md)) means little without the chance that noise
alone would reach it, and the caller also has to pick the frequencies. Scargle gave an exponential
false-alarm form for a power normalized by the true noise variance; the standard normalization
divides by the sample's own `Σy²` instead, so its noise distribution is a Beta, not an exponential.
For the grid, the usual choice is a spacing finer than `1/T` (the peak width) up to a maximum
frequency the caller trusts.

## Decision

- `lomb_scargle_false_alarm(power, num_samples, *, num_frequencies=1, center=True)` (C#
  `Spectral.LombScargleFalseAlarm`) for the **standard** normalization only. With `N` samples of
  white Gaussian noise, the standard value `z` at one frequency is `Beta(1, (N − d)/2)`, `d = 3`
  when centered and `d = 2` when not, so `P₁(z) = (1 − z)^((N − d)/2)` is the chance of a value
  above `z`. Over `M` independent frequencies the chance that any exceeds `z` is
  `1 − (1 − P₁)^M`, computed as `−expm1(M·log1p(−P₁))`.
  - The Beta form is exact when the fitted cosine and sine are orthogonal to the constant (not
    centered; or centered with evenly spaced times at a bin `k·fs/N`, `0 < k < N/2`) and close
    otherwise. A grid's frequencies are not independent; `M ≈ f_max·T` is the usual estimate, and
    choosing it is the caller's.
  - `z` must be in `[0, 1]`; `N ≥ d + 1` so the exponent is positive; `M ≥ 1`.
  - The power and psd normalizations need the true noise variance, which the function does not
    take; they are not supported.
- `lomb_scargle_frequencies(times, *, oversampling=5.0, max_frequency=None)` (C#
  `Spectral.LombScargleFrequencies`): `T = max(t) − min(t) > 0`, spacing
  `Δ = 1/(oversampling·T)`, frequencies `k·Δ` for `k = 1 … K`, `K = ⌊f_max/Δ + 1e-9⌋`; the default
  `f_max` is `N/(2T)`, the Nyquist frequency of `N` evenly spaced samples over `T`. `oversampling`
  and `f_max` positive and finite; `K` at most `10⁷`; `K = 0` gives an empty grid.

## Consequences

- A peak can be reported with a false-alarm probability that both languages compute the same way.
- Bootstrap estimates and the Baluev bound are not here; they can be added beside it.
