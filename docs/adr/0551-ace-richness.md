# ADR 0551: The ACE richness

Status: accepted, 2026-11-21.

## Context

Chao and Lee (1992) estimate the number of kinds from the rare ones: kinds seen 10 times or
fewer. Their coverage `C = 1 − F₁/N_rare` says how much of the rare group the sample has
seen, and a squared coefficient of variation `γ²` corrects for uneven rare kinds. This is
the abundance-based coverage estimator, ACE, with the usual cut-off of 10.

## Decision

- **The API.**
  - Python: `ace_richness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.AceRichness(ReadOnlySpan<double> samples)`.
- **The value.**
  - Abundant kinds have values above 10, rare kinds values 1 to 10. `S_abund` and `S_rare`
    count them, `N_rare` sums the rare values, `F₁` counts the values equal to 1 and
    `P = Σ xᵢ(xᵢ − 1)` runs over the rare values; sums in record order.
  - `C = 1 − F₁/N_rare` and `γ² = max(S_rare/C · P/(N_rare(N_rare − 1)) − 1, 0)`, formed
    left to right.
  - `S = S_abund + S_rare/C + F₁/C · γ²`; with no rare kinds, `S = S_abund`.
  - At least the count of values above 0.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.
  - When there are rare kinds, not all of them singletons, so `C > 0` (otherwise
    `invalid_argument`); then `N_rare ≥ 2`.

## Consequences

- One pass for the checks, one for the counts.
- The cut-off is fixed at 10; another cut-off would be a new parameter.
- **Vectors.**
  - The generator forms the value exactly in rationals, from the counts `Fᵢ` of each value.
  - The tolerance is `abs 1e-13, rel 1e-12`.
