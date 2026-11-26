# ADR 0620: Eberhardt's index

Status: accepted, 2026-11-26.

## Context

Pielou's index (ADR 0619) needs the density of the pattern, which is usually what a survey
is trying to find. Eberhardt (1967) used the distances `u` from points placed at random to
the nearest individual on their own: `I = n Σu²/(Σu)²`, the mean square over the square of
the mean, which does not change when every distance is scaled. At random `u` follows a
Rayleigh distribution, for which the ratio tends to `4/π ≈ 1.273`; it is larger for a
clumped pattern, where the distances spread out. By the Cauchy–Schwarz inequality it lies
in [1, n].

## Decision

- **The API.**
  - Python: `eberhardt_index(point_distances)` in `measurements`, giving a float.
  - C#: `Measurements.EberhardtIndex(ReadOnlySpan<double> pointDistances)`.
- **The form.** With `t` the largest distance, `s_1 = Σ u/t` and `s_2 = Σ(u/t)²` added in
  order, the value is `n s_2/(s_1 s_1)`, held to [1, n].
- **Which variance (review, 2026-11-26).** The value is `n Σu²/(Σu)²`, which is
  `σ²/ū² + 1` with the variance `σ²` divided by `n`. Krebs (Ecological Methodology, 2017
  web edition, eq. 6.14) writes Eberhardt's index as `(s/ū)² + 1` with `s` the "observed
  standard deviation". His worked example (Box 5.2 data, `n = 16`, `s² = 13.020`) shows he
  divides by `n − 1`, which gives 1.14 where this form gives 1.130. Neither Eberhardt (1967)
  nor Hines and Hines (1979) could be read, so which form they print is still not
  confirmed. SignalForge keeps the moment ratio, because it is defined for `n = 1`, has the
  exact bounds [1, n], and has the same large-sample value 4/π. A caller who wants Krebs'
  value can form `1 + (I − 1) n/(n − 1)`. The vector `krebs_spruce` holds Krebs' 16
  distances. Its generator checks his published sums, and checks that the conversion gives
  his 1.14.
- **The rules.**
  - `point_distances` one-dimensional, real, finite, at least 0, with a value above 0.
  - Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the value with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the two sums.
