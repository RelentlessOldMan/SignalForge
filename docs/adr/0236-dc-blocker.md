# ADR 0236: DC blocker

Status: accepted, 2026-11-17.

## Context

Removing a slowly drifting offset with almost no effect on the band of interest is usually done
with the one-pole, one-zero high-pass `H(z) = (1 − z⁻¹)/(1 − p z⁻¹)`. ADR 0014 names it as a use of
IIR filters. It is cheaper than a designed high-pass and needs no cutoff design.

## Decision

- **The API.**
  - Python: `dc_blocker(samples, pole)` in `dsp`.
  - C#: `Dsp.DcBlocker(samples, pole)`, for real or complex samples.
- **The value.**
  - `y[n] = (x[n] − x[n−1]) + p·y[n−1]`, with `x[−1] = y[−1] = 0`, computed in that order.
  - The filter starts from rest, so a constant input decays as `p^n` from its first value
    rather than being removed at once.
  - The gain is 0 at DC and `2/(1 + p)` at Nyquist. The −3 dB point is approximately
    `(1 − p)·fs/(2π)` for `p` near 1.
- **The rules.**
  - `pole` must be finite with `0 ≤ pole < 1`.
  - The samples must be finite and non-empty.

## Consequences

- **Vectors.** The expected values come from the impulse response `h[0] = 1`,
  `h[k] = (p − 1)·p^(k−1)` for `k ≥ 1`. It is convolved with the input in exact rational
  arithmetic, using poles that are exact binary fractions.
