# ADR 0599: Petraitis' specific overlap

Status: accepted, 2026-11-23.

## Context

Petraitis (1979) measured how well one record of use, with shares `p_i = x_i/Σx`, fits a
second, with shares `q_i = y_i/Σy`, by the likelihood of the first under the second:
`SO = exp(E)`, `E = Σ p_i ln q_i − Σ p_i ln p_i = Σ p_i ln(q_i/p_i)`, the sums over the kinds
with `p_i > 0`. By Gibbs' inequality `E ≤ 0`, so `SO` runs from 0 to 1, with 1 when the
shares are the same. It is not symmetric: `x` is the record being fitted.

## Decision

- **The API.**
  - Python: `petraitis_overlap(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.PetraitisOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
- **The form.** Each record is first divided by its largest value, then by its sum, added
  in order, to give the shares. `E` is added in order as `p_i (ln q_i − ln p_i)` over the
  kinds with `p_i > 0`; the two logarithms are taken apart so their ratio cannot overflow.
  The value is `exp(E)`, held at 1 from above.
- **A kind that `x` uses and `y` does not.** Then `ln q_i = −∞`, `E = −∞`, and the value is
  its limit, 0. This also holds when `q_i` underflows to 0. The Next entry that proposed
  this measure asked for an error here instead; the limit is the defined value and needs no
  extra rule.
- **The rules.** As for `pianka_overlap`: each record one-dimensional, real, finite, at
  least 0, not empty, with a value above 0; the same length. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms the shares with fractions and `E` with 60-digit decimal
    logarithms, then its exponential.
  - Each hand case is also checked against its closed form.
  - The tolerance is `abs 1e-14, rel 1e-14`.
