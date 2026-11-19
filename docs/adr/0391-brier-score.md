# ADR 0391: The Brier score

Status: accepted, 2026-11-19.

## Context

Brier (1950) scored probability forecasts of a binary event by the mean squared difference
between the forecast probability and the outcome. Unlike the measures of ADRs 0385 to 0390 it
grades a probability, not a hard decision, and it is a proper score: a forecaster minimises
its expectation by stating their true belief.

## Decision

- **The API.**
  - Python: `brier_score(outcome, probability)` in `measurements`, giving a float.
  - C#: `Measurements.BrierScore(ReadOnlySpan<double> outcome,
    ReadOnlySpan<double> probability)`.
  - `outcome` holds 0 and 1, 1 for the event happening; `probability` is the forecast
    probability of the event.
- **The value.**
  - `BS = (1/N)·Σ (pᵢ − yᵢ)²`, from 0 (perfect) to 1. The squares are summed in order, then
    divided by `N`.
  - Only the binary form is built; Brier's form over several classes is not.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1.
  - Every outcome 0 or 1; every probability finite and in `[0, 1]`.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator sums the squares exactly in rationals and rounds once.
  - The tolerance is `abs 1e-15, rel 1e-13`, for a sum in order against the exact one.
