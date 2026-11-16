# ADR 0142: Tristimulus

Status: accepted, 2026-11-16. It builds on the harmonic series (ADR 0139).

## Context

The tristimulus describes the balance of a harmonic sound in three numbers:

- the share in the fundamental;
- the share in harmonics 2 to 4;
- the share in harmonics 5 and up.

The original definition sums harmonic amplitudes, not powers. Later uses differ. SignalForge
tones carry PSD heights, which are powers.

## Decision

- **The API.**
  - Python: `tristimulus(heights, orders) -> Tristimulus(first, second, third)`.
  - C#: `Spectral.Tristimulus(heights, orders)`, returning the record
    `Tristimulus(First, Second, Third)`, where `orders` is a span of `int`.
- **The value.**
  - It uses amplitudes, as the original definition does: `a_i = sqrt(h_i)` from each power
    height.
  - With `A = Σ a_i` over orders ≥ 1:
    - `first = a(order 1)/A`;
    - `second = Σ a(orders 2–4)/A`;
    - `third = Σ a(orders ≥ 5)/A`.
  - The three shares sum to 1. Tones that share an order are summed.
  - Order 0 (unmatched) is left out.
- **The rules.**
  - The arrays are 1-D and the same length.
  - Heights are finite and `≥ 0`.
  - Orders are whole numbers `≥ 0`. Python also accepts whole-valued floats.
  - `A` must be above 0.
  - Anything else is `invalid_argument`.

## Consequences

- **A missing fundamental gives `first = 0`.**
- **Vectors.** They are worked by hand in Fractions, with heights that are perfect squares so
  the amplitudes are exact:
  - all three bands.
  - the fundamental only.
  - a missing fundamental.
  - an unmatched tone.
  - the errors.
- **Tests.**
  - Scaling the heights leaves the shares unchanged.
  - The shares sum to 1.
  - A sawtooth's harmonic amplitudes `1/m` match the shares computed directly.
