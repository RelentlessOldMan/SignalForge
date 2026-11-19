# ADR 0392: The log loss

Status: accepted, 2026-11-19.

## Context

The log loss, or binary cross-entropy, is the negative mean log-likelihood of the outcomes
under the forecast probabilities. Like the Brier score (ADR 0391) it is a proper score, but it
punishes a confident wrong forecast without bound.

## Decision

- **The API.**
  - Python: `log_loss(outcome, probability)` in `measurements`, giving a float.
  - C#: `Measurements.LogLoss(ReadOnlySpan<double> outcome, ReadOnlySpan<double> probability)`.
  - The records as for the Brier score.
- **The value.**
  - `LL = −(1/N)·Σ ℓᵢ`, with `ℓᵢ = ln pᵢ` where `yᵢ = 1` and `ℓᵢ = ln(1 − pᵢ)` where `yᵢ = 0`.
    The natural log, in nats; from 0 up.
  - Only the term the outcome picks is formed, so a certain right forecast gives exactly 0
    and never `0·(−∞)`.
  - `1 − pᵢ` is formed in `double`, then its log. The terms are summed in order, negated and
    divided by `N`.
  - No clipping of the probabilities: a caller who wants a floor applies it first.
- **The rules.**
  - Both records one-dimensional, the same length, at least 1.
  - Every outcome 0 or 1; every probability finite and in `[0, 1]`.
  - A certain wrong forecast (`p = 0` with `y = 1`, or `p = 1` with `y = 0`) is an error: the
    loss would be infinite.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator takes each term with `math.log` and sums with `math.fsum`; the hand cases
    are multiples of `ln 2` and `ln 4`.
  - The tolerance is `abs 1e-15, rel 1e-13`, for the platform log and a sum in order.
