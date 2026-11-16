# ADR 0140: Inharmonicity

Status: accepted, 2026-11-16. It builds on the harmonic series (ADR 0139).

## Context

A stiff string's partials sit above exact multiples of the fundamental. Inharmonicity measures
how far they sit. The timbre descriptors used in audio take each partial's distance from its
harmonic, `|t − m·f0|`, and weight it by the partial's power. They scale by `2/f0`, so the
result runs from 0 to 1 when no partial is more than half a fundamental away.

## Decision

- **The API.**
  - Python: `inharmonicity(frequencies, heights, fundamental, orders) -> float`.
  - C#: `Spectral.Inharmonicity(frequencies, heights, fundamental, orders)`, where `orders` is
    a span of `int`.
  - The arguments are the tones' frequencies and heights, as from `find_tones`, and the
    `harmonic_series` fundamental and orders for those tones.
- **The value.**
  - `inharmonicity = (2/f0)·Σ h_i |t_i − m_i f0| / Σ h_i` over the tones with `m_i ≥ 1`.
  - Tones with order 0 are unmatched and are left out.
  - The heights are powers, PSD values, so they weight the sum as the power weighting does.
- **The rules.**
  - The three arrays are 1-D and the same length.
  - `frequencies` are finite and positive, and `heights` are finite and non-negative.
  - `orders` are whole numbers `≥ 0`. Python also accepts whole-valued floats.
  - `fundamental` is finite and positive.
  - At least one tone has order `≥ 1`, and the heights of those tones sum to more than 0.
  - Anything else is `invalid_argument`.

## Consequences

- **Units.** The value is dimensionless. 0 means exact harmonics. A partial half a fundamental
  away gives 1.
- **Vectors.** These are worked by hand in Fractions:
  - exact harmonics.
  - detuned and weighted harmonics.
  - an unmatched tone that is left out.
  - a zero-height tone.
  - the half-fundamental extreme.
  - the errors.
- **Tests.**
  - Scaling the frequencies and the fundamental together leaves the value unchanged.
  - Scaling the heights leaves it unchanged.
  - A stiff-string series `m·f0·sqrt(1 + B m²)` gives a value that grows with `B`.
