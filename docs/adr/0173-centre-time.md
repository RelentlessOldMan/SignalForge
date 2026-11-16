# ADR 0173: Centre time

Status: accepted, 2026-11-16. It completes the ISO 3382 energy parameters, with the
reverberation time (ADR 0171) and clarity and definition (ADR 0172).

## Context

The centre time `T_s` is the energy centroid of an impulse response, `Σ t|h|² / Σ |h|²`. It
looks like the temporal centroid (ADR 0147), but that one weights by the amplitude envelope,
not the energy. The early decay time (EDT) is the reverberation fit over 0 to −10 dB.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `centre_time(impulse_response, sample_rate)`.
  - C#: `Measurements.CentreTime(impulseResponse, sampleRate)`.
  - Both return seconds.
- **The definition.** `T_s = Σ (n/fs)·|h[n]|² / Σ |h[n]|²`, with the origin at index 0, as in
  ADR 0172.
- **The early decay time.** There is no new function. EDT is `reverberation_time(h, fs,
  start_db=0, stop_db=-10)`.
  - With `start_db = 0`, the fit starts at `n = 0`, because `d[0] = 0 ≤ 0`.
  - This is the ISO evaluation range, and the factor 6 is the `−60/m` already in ADR 0171.
- **The rules.**
  - The response is one-dimensional, finite, not empty and not all zero.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors are exact sums.** They use hand sums in fractions and the geometric closed form
  for `h[n] = r^n` over `L` samples, in 50-digit `decimal`:
  `Σ n·qⁿ = q(1 − (L)q^(L−1) + (L − 1)q^L)/(1 − q)²`, with `q = r²`.
- **A test pins EDT.** It confirms that EDT through `reverberation_time` equals `60/(−20
  log10 r·fs)` for a long geometric decay.
