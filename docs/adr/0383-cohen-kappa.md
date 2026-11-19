# ADR 0383: Cohen's kappa

Status: accepted, 2026-11-19.

## Context

Cohen (1960) measured the agreement of two raters who each put the same `N` items into
categories, correcting the share of items they agree on by the agreement expected if each
labelled at random at their own overall rates. In a signal framework the raters are often
two classifiers or detectors labelling the same frames.

## Decision

- **The API.**
  - Python: `cohen_kappa(a, b)` in `measurements`, `a` and `b` the two raters' labels, giving
    a float.
  - C#: `Measurements.CohenKappa(ReadOnlySpan<double> a, ReadOnlySpan<double> b)`.
  - Labels are numbers, as every record in SignalForge is; the categories are the distinct
    values in either record, compared with `==`.
- **The value.**
  - `A` is the number of items with `a_i = b_i`; `a_c` and `b_c` count category `c` in each
    record, and `E = Σ_c a_c b_c`.
  - `p_o = A/N`, `p_e = E/N²`, and `κ = (p_o − p_e)/(1 − p_e) = (N A − E)/(N² − E)`.
  - The second form is a ratio of whole numbers, exact until they pass `2⁵³`, and is the
    one computed.
- **The rules.**
  - `a` and `b` real, one-dimensional, finite and the same length, at least 1.
  - `p_e < 1`: not both raters using one and the same category for every item.

## Consequences

- The cost is a sort of each record.
- **Vectors.**
  - The generator counts in integers; one case is the usual 2 × 2 textbook table with
    `p_o = 0.7`, `p_e = 0.5`, `κ = 0.4`.
  - The tolerance is `abs 1e-15, rel 1e-15`.
