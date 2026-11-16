# ADR 0162: ERB-spaced center frequencies

Status: accepted, 2026-11-16. It builds on the ERB scale (ADR 0160), for gammatone filterbanks
(ADR 0161).

## Context

A gammatone filterbank puts its center frequencies at equal steps of ERB rate. Implementations
differ on three points:

- whether both endpoints are included;
- the order: Slaney's toolbox returns them high to low;
- whether the endpoints come back exactly or after a round trip through the scale.

## Decision

- **The API.**
  - Python: `erb_space(min_frequency, max_frequency, n_frequencies)`, in `units`.
  - C#: `Units.ErbSpace(minFrequency, maxFrequency, nFrequencies)`, returning `double[]`.
- **The values.**
  - `E_lo = hz_to_erb_rate(min)` and `E_hi = hz_to_erb_rate(max)`.
  - `f_i = erb_rate_to_hz(E_lo + (E_hi − E_lo)·i/(n − 1))` for `i = 0 … n − 1`, in ascending
    order, like `linspace`.
  - The first value is exactly `min` and the last is exactly `max`, not round-tripped.
  - With `n = 1` the result is `[min]`.
- **The rules.**
  - `0 ≤ min < max`, both finite.
  - `n_frequencies ≥ 1` is an integer.
  - Anything else is `invalid_argument`.

## Consequences

- **A filterbank is a loop.** For example, `[gammatone(f, fs, L) for f in erb_space(lo, hi, n)]`.
- **Vectors come from the closed forms.** They are computed in 50-digit `decimal`, with the ERB
  rate of ADR 0160. Choosing `min = 0` and `max = (1000/4.37)·(10^k − 1)` puts the points at
  `E = 21.4·k·i/(n − 1)`. The cases are:
  - several counts;
  - `n = 1`;
  - `n = 2`, which gives only the endpoints;
  - a non-zero minimum;
  - the errors.
