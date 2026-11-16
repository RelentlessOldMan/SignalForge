# ADR 0160: ERB scale

Status: accepted, 2026-11-16. It sits beside the mel scale (ADR 0154).

## Context

The equivalent rectangular bandwidth (ERB) of the auditory filter, and the ERB-rate scale
built on it, come from Glasberg & Moore (1990). Gammatone filterbanks and loudness models use
them. Implementations differ on two points:

- the constants: the published, rounded `21.4`, or the exact
  `1000/(24.7·4.37)/log10(e) ≈ 21.33` that follows from integrating `1/ERB`;
- which name means the bandwidth and which means the rate.

## Decision

- **The API.** In `units`:
  - Python: `hz_to_erb_rate(hz)`, `erb_rate_to_hz(erb)` and `erb_bandwidth(hz)`.
  - C#: `Units.HzToErbRate`, `Units.ErbRateToHz` and `Units.ErbBandwidth`.
  - Python takes scalars or arrays, as the mel functions do.
- **The formulas.** These use the published constants, as Glasberg & Moore print them and as
  most libraries use them.
  - The bandwidth is `ERB(f) = 24.7·(4.37·f/1000 + 1)` Hz.
  - The rate is `E(f) = 21.4·log10(4.37·f/1000 + 1)`, in ERB numbers ("Cams").
  - The inverse rate is `f = (10^(E/21.4) − 1)·1000/4.37`.
- **The rules.** Every input must be finite and `≥ 0`. Anything else is `invalid_argument`.

## Consequences

- **The rate is approximate.** Because `21.4` is rounded, `dE/df` is not exactly `1/ERB(f)`.
  The difference is about 0.32 % at every `f`: `dE/df·ERB(f) = 21.4·24.7·4.37/(1000·ln 10) ≈
  1.0032`. This is documented and not corrected.
- **Vectors come from the closed forms.**
  - The bandwidth is exact: `ERB(0) = 24.7` and `ERB(1000) = 132.639`.
  - The rate and its inverse are computed in 50-digit `decimal` from the float arguments, with
    `f = (1000/4.37)·(10^k − 1)` giving `E = 21.4·k`.
  - There are also the errors.
