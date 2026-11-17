# ADR 0188: Teager-Kaiser energy

Status: accepted, 2026-11-16.

## Context

The Teager-Kaiser energy operator `ψ[n] = x[n]² − x[n−1]·x[n+1]` (Kaiser, 1990) tracks the
energy needed to generate a signal. For `A·cos(Ωn + φ)` it is exactly `A²·sin²Ω`, so it follows
both amplitude and frequency within three samples. It is used for:

- AM-FM demodulation;
- onset detection;
- detecting spikes in noise.

Implementations differ on three points:

- whether they pad the ends (with zeros or by repeating values);
- the complex form;
- the shortest input.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `teager_energy(samples)`.
  - C#: `Measurements.TeagerEnergy(samples)`.
- **The definition.** `ψ[n] = |x[n]|² − Re(x[n−1]·conj x[n+1])` for `n = 1 … N−2`.
  - The result has `N − 2` real values, with no padding: `ψ[n]` sits at index `n − 1`.
  - For real input this is `x[n]² − x[n−1]·x[n+1]`.
  - For `A·e^{jΩn}` the complex form gives `2A²·sin²Ω`. This is the Hamila (1999) complex
    operator, and it is twice the real cosine's value, because a cosine's energy is split
    between two complex exponentials.
  - The value can be negative.
- **The rules.**
  - The input is one-dimensional and finite, with at least three samples.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** They come from the trigonometric identities and from hand sums:
  - `A²·sin²Ω` for a cosine;
  - `2A²·sin²Ω` for a complex exponential;
  - zero for a geometric sequence;
  - `1` for a ramp;
  - short integer and complex hand sums.
