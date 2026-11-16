# ADR 0169: Percentile (exceedance) levels

Status: accepted, 2026-11-16. It reads a series from the time weighting (ADR 0166).

## Context

Environmental noise is often reported as `L_N`, the level exceeded `N` % of the time. L10 is
the loud events, L50 the median and L90 the background. The level is read from a series of
time-weighted values. Implementations differ on three points:

- the quantile definition (nearest rank, or one of several interpolations);
- whether the result is in dB or in power;
- the range of `N`.

## Decision

- **The API.** In `measurements`:
  - Python: `exceedance_levels(powers, percents)`.
  - C#: `Measurements.ExceedanceLevels(powers, percents)`.
  - Both return one value per percent, in the order given.
- **The definition.** `L_N` is the `q = 1 − N/100` quantile of the values, computed by linear
  interpolation between order statistics (Hyndman and Fan type 7, NumPy's default):
  - sort ascending to `s_0 ≤ … ≤ s_{n−1}`;
  - `h = (n − 1)·q`;
  - `L = s_⌊h⌋ + (h − ⌊h⌋)·(s_⌊h⌋+1 − s_⌊h⌋)`, which is `s_{n−1}` when `h = n − 1`.

  As a result, `L_0` is the maximum and `L_100` is the minimum.
- **Power in, power out.** The interpolation is done on the powers, not in dB. The caller takes
  dB with `lin_to_db`. Because the quantile is monotonic, the order statistics themselves are
  the same either way; only the interpolated values between them differ.
- **The rules.**
  - `powers` is one-dimensional, not empty, finite and `≥ 0`.
  - `percents` is one-dimensional and finite, each in `[0, 100]`. It may be empty, which gives an
    empty result.
  - Anything else is `invalid_argument`.

## Consequences

- **The result is not a dB interpolation.** It differs slightly from a meter that interpolates
  in dB, but only between samples.
- **Vectors come from hand-sorted small series.** The interpolation is done in exact
  fractions. The cases are:
  - an odd and an even length;
  - repeated values;
  - the extremes 0 and 100;
  - a single value;
  - an empty `percents`;
  - the errors.
