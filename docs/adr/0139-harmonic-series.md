# ADR 0139: Harmonic series

Status: accepted, 2026-11-16. It builds on find tones (ADR 0137).

## Context

A list of tones often comes from one periodic source: a fundamental and some of its harmonics.
The fundamental itself may be missing or weak. Estimators of the fundamental try candidates,
count the tones each one explains, and refine the winner. They differ on three things:

- where the candidates come from;
- how ties are broken, since `f0/2` explains every tone that `f0` does;
- how the winner is refined.

## Decision

- **The API.**
  - Python: `harmonic_series(frequencies, tolerance, *, max_order=10)`, returning
    `HarmonicSeries(fundamental, orders, matched)`.
  - C#: `Spectral.HarmonicSeries(frequencies, tolerance, maxOrder)`, returning the record
    `HarmonicSeries(Fundamental, Orders, Matched)`.
  - `frequencies` are tone frequencies in Hz, such as those from `find_tones`, in any order.
- **The candidates.** The candidates are `t_i / m` for every tone `t_i` and every
  `m = 1..max_order`.
- **Matching.** A tone `t` matches candidate `c` at order `m = ⌊t/c + 1/2⌋` when
  `1 ≤ m ≤ max_order` and `|t − m·c| ≤ tolerance`.
- **The winner.** The candidate that matches the most tones wins. Ties go to the highest
  candidate, so a subharmonic wins only when it explains more tones.
- **The refinement.** `fundamental = Σ m_i t_i / Σ m_i²` over the winner's matched tones. It is
  the least-squares fit of `t_i ≈ m_i·f0`.
- **The orders.**
  - `orders[i]` is the winner's order for tone `i`, or 0 when the tone is unmatched. The tones
    are not matched again against the refined fundamental.
  - `matched` is the number of matched tones.
- **The rules.**
  - `frequencies` must be a 1-D array of at least one finite, positive value.
  - `tolerance` must be finite and positive, in Hz.
  - `max_order` must be an integer, at least 1.
  - Anything else is `invalid_argument`.

## Consequences

- **The cost.** There are `n·max_order` candidates, and each is checked against `n` tones. That
  is fine for the tens of tones that `find_tones` gives.
- **A missing fundamental is found.** For example, 200, 300 and 400 Hz give 100 Hz.
- **A stray tone can pull the answer down.** A stray tone that is a multiple of a subharmonic
  makes that subharmonic win, because it explains more tones. Choosing `max_order` limits this.
- **Vectors.** These are worked by hand:
  - exact harmonics, where the subharmonic ties and loses.
  - detuned harmonics, whose least-squares fundamental is a fraction.
  - a stray tone, at two values of `max_order`.
  - a missing fundamental.
  - a single tone.
  - the errors.
- **Tests.**
  - The result does not depend on the order of the tones.
  - Scaling every frequency and the tolerance scales the fundamental.
  - The four strongest tones of a symmetrically clipped sine, from `find_tones`, match
    odd orders of its frequency.
