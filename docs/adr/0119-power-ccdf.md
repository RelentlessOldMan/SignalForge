# ADR 0119: Power CCDF

Status: accepted, 2026-11-16. It extends power statistics (conventions: Power, amplitude, and dB).

## Context

PAPR is a single sample, the peak, and it grows with the record length. Waveforms are compared
by the complementary cumulative distribution function (CCDF) of instantaneous power instead: the
fraction of samples whose power exceeds the mean by a given level. It is also read the other way,
as the level exceeded with a given probability (the "PAPR at 0.01 %" of OFDM and CDMA
specifications). The brief asks for it, and conventions already say it uses `|x|²`.

## Decision

- Python `power_ccdf(samples, levels_db)` and C# `Measurements.PowerCcdf(...)`, for real or
  complex samples.
  - The instantaneous power is `p[n] = |x[n]|²`, and `P̄` is its mean, as for `power_stats`.
  - For each level `L` (dB, any order), the probability is `#{n : p[n] > P̄·10^{L/10}} / N`.
    The comparison is **strict**, so a sample exactly on the threshold does not count. A constant
    envelope therefore gives 0 at 0 dB.
  - The result is `PowerCcdf(mean_power, levels_db, probabilities)`, with the levels in the order
    given.
- Python `power_ccdf_level(samples, probability)` and C# `Measurements.PowerCcdfLevel(...)` read
  it the other way. They return the smallest level, in dB above `P̄`, whose CCDF is at most
  `probability`.
  - Let `m = ⌊probability·N⌋`, the number of samples allowed above. The threshold is the
    `(m + 1)`-th largest power, so the result is `10·log10(p_(m+1)/P̄)`. Ties are counted as
    `power_ccdf` counts them. This is `−∞` when that power is 0.
  - A probability below `1/N` gives `m = 0`, the peak, so the result is the PAPR.
  - `0 < probability < 1` is required.
- **The rules.**
  - The samples must be one-dimensional, non-empty and finite, and `P̄ > 0`.
  - The levels must be a non-empty one-dimensional list of finite values.
  - Anything else is `invalid_argument`.

## Consequences

- **No curve function.** The CCDF is not sampled on a default grid. The caller picks the
  levels, so the result is the same in both languages, with no grid convention to agree on.
- **Vectors.** These are counted by hand on short integer-power sets, where `P̄` and the
  thresholds are exact. They include ties at 0 dB (exactly `P̄`), all-equal powers, and a zero
  sample for `−∞`.
  - Levels that are not 0 dB are kept away from any power, because `10^{L/10}` rounds
    differently from library to library.
- **Tests.**
  - Complex Gaussian noise has `P(p > g·E p) = exp(−g)`, and real Gaussian noise has
    `erfc(√(g/2))`. These are checked with a binomial tolerance.
  - A complex tone has a CCDF of 0 at every level above 0 dB.
  - `power_ccdf_level` and `power_ccdf` are inverses of each other on the same samples, to within
    the rounding of the level through dB.
