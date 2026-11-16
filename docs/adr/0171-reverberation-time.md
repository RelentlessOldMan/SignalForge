# ADR 0171: Reverberation time

Status: accepted, 2026-11-16. It belongs with the room-acoustics measures beside the
octave-band levels (ADR 0168).

## Context

ISO 3382 measures reverberation from an impulse response `h` in two steps:

- the Schroeder backward-integrated energy decay curve;
- a straight line fitted to part of that curve and extrapolated to a 60 dB decay. With an
  evaluation range from −5 to −25 dB this gives T20; to −35 dB it gives T30.

Implementations differ on four points:

- which samples enter the fit;
- the fit itself;
- what happens when the decay never reaches the lower level;
- noise compensation.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `schroeder_decay(impulse_response)`; C#: `Measurements.SchroederDecay`.
  - Python: `reverberation_time(impulse_response, sample_rate, *, start_db=-5.0,
    stop_db=-25.0)`; C#: `Measurements.ReverberationTime(..., startDb = -5, stopDb = -25)`.
- **The curve.** `d[n] = 10·log10(E[n]/E[0])`, where `E[n] = Σ_{k ≥ n} |h[k]|²` is the backward
  sum over the whole input.
  - `d[0] = 0`.
  - A tail of exact zeros gives `−inf`.
  - There is no truncation correction and no noise compensation. The caller trims the
    response first.
- **The fit.**
  - `n1` is the first index with `d[n] ≤ start_db`, and `n2` is the first index with
    `d[n] ≤ stop_db`.
  - The fit uses the samples `n1 ≤ n < n2`. There must be at least two of them.
  - The line is the ordinary least-squares fit of `d[n]` on `t = n/fs`, with slope `m` in
    dB/s. The result is `T = −60/m` seconds, and `m` must be negative.
- **The rules.**
  - The response is one-dimensional, finite, not empty, and not all zero.
  - `sample_rate` is finite and positive.
  - `stop_db < start_db ≤ 0`, both finite.
  - It is `invalid_argument` if the curve never reaches `stop_db`, if fewer than two samples
    lie in the range, or if the slope is not negative.

## Consequences

- **Thresholds near a sample can differ between languages.** A level within rounding of a
  threshold could pick a different `n1` or `n2`. The vectors keep every curve value well away
  from both levels.
- **Vectors come from an independent decimal computation.** The generator uses:
  - the exact geometric tail of `h[n] = r^n` over `N` samples,
    `E[n]/E[0] = (r^(2n) − r^(2N))/(1 − r^(2N))`;
  - the least-squares slope, both in 50-digit `decimal`.

  For long `N` it also asserts that the result lies close to `T = 60/(−20·log10 r · fs)`.
