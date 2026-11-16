# ADR 0183: Noise-compensated decay

Status: accepted, 2026-11-16. It goes with the Schroeder decay of ADR 0171.

## Context

A measured impulse response ends in background noise. Backward integration adds that noise to
every point of the decay, which bends the late part of the curve upward. ISO 3382-1 §5.3.3
allows the noise to be compensated by subtracting an estimate of its power before integrating.
Implementations differ on four points:

- where the estimate comes from;
- what happens over the estimation window itself;
- what a negative integral gives;
- what is returned.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `noise_compensated_decay(impulse_response, *, tail=0.1)`.
  - C#: `Measurements.NoiseCompensatedDecay(impulseResponse, tail = 0.1)`.
- **The estimate.**
  - The noise window is the last `M = ⌊tail·N + 1/2⌋` samples, and `1 ≤ M < N` is required.
  - The noise power is `ν = Σ_{k ≥ N−M} |h[k]|² / M`.
- **The decay.**
  - `E[n] = Σ_{k=n}^{N−M−1} (|h[k]|² − ν)`, for `0 ≤ n < N − M`.
  - The result is `10·log10(E[n]/E[0])`, one value for each sample before the noise window, so
    there are `N − M` values.
  - The window is left out of the integral. Over the window itself the compensated sum is zero
    by construction, and computing it there would only return rounding noise.
- **Zero and negative energy.**
  - Where `E[n] ≤ 0` the value is `−inf`, meaning the response has sunk into the noise.
  - `E[0] ≤ 0` is `invalid_argument`.
- **The rules.**
  - The response is one-dimensional, finite and not empty.
  - `tail` is finite and in `(0, 1)`.
  - Anything else is `invalid_argument`.

## Consequences

- **Use with reverberation time.** The result can be fitted like `schroeder_decay`'s. The fit
  levels of `reverberation_time` are not applied to it here, and choosing the noise window is the
  caller's job.
- **Vectors.**
  - They are exact rational sums of the samples as stored, worked in fractions.
  - The cases are a dyadic decay with a ±1/16 tail, a decay with noise throughout, complex
    input, and a dip below the noise floor that gives `−inf`.
  - Every `E[n]` is exactly zero (dyadic cases) or at least `1e−6` of the sum of
    `|h[k]|² − ν` that it adds up, so that float rounding cannot change its sign.
