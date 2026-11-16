# ADR 0172: Clarity and definition

Status: accepted, 2026-11-16. It goes with the reverberation time (ADR 0171).

## Context

ISO 3382 defines two early-to-late energy measures from an impulse response:

- clarity, `C_te = 10·log10(E_early/E_late)`: C80 for music and C50 for speech;
- definition, `D50 = E_early/E_total`.

Implementations differ on four points:

- where the response starts (index 0, the peak, or a −20 dB onset);
- how the boundary `t·fs` is rounded;
- which side of the boundary its own sample falls on;
- what a response with no late energy gives.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `clarity(impulse_response, sample_rate, *, time=0.08)`; C#: `Measurements.Clarity`.
  - Python: `definition(impulse_response, sample_rate, *, time=0.05)`; C#:
    `Measurements.Definition`.
- **The start.** The response starts at index 0; the caller trims it to the direct sound.
  Onset detection is not done here, because the rules for it vary.
- **The boundary.** `N = ⌊time·fs + 1/2⌋`, the same rounding as `block_leq` (ADR 0170).
  - The early energy is `E_early = Σ_{n<N} |h[n]|²`, so sample `N` itself is late.
  - The late energy is `E_late = Σ_{n≥N} |h[n]|²`.
  - `N` may exceed the length, in which case all the energy is early.
- **The results.**
  - Clarity is `10·log10(E_early/E_late)`. It is `+inf` when `E_late = 0` and `−inf` when
    `E_early = 0`.
  - Definition is `E_early/(E_early + E_late)`, in `[0, 1]`.
- **The rules.**
  - The response is one-dimensional, finite, not empty and not all zero.
  - `sample_rate` and `time` are finite and positive, and `N ≥ 1`.
  - Anything else is `invalid_argument`.

## Consequences

- **The caller trims to the direct sound.** A response with a pre-delay must be trimmed first,
  or both results are skewed.
- **Vectors are exact sums.** They use hand sums in fractions and geometric decays
  `h[n] = r^n`, with
  `C = 10·log10((1 − q^N)/(q^N − q^L))`, where `q = r²` and `L` is the length, in 50-digit
  `decimal`.
