# ADR 0506: Cohen's h

Status: accepted, 2026-11-20.

## Context

Cohen's h is the effect size for two proportions: the difference of their arcsine square
root transforms, `2·asin(√p₁) − 2·asin(√p₂)`, with `p₁ = TP/(TP + FP)` the share of truth
1s where the decision (the exposure) is 1 and `p₂ = FN/(FN + TN)` the share where it is 0.

## Decision

- **The API.**
  - Python: `cohen_h(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.CohenH(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
- **The value.**
  - `asin(√(a/(a + b)))` equals `atan2(√a, √b)` for counts `a, b ≥ 0` not both 0, and
    the second form keeps full accuracy near a share of 1, where `asin` is steep. So
    `h = 2·(atan2(√TP, √FP) − atan2(√FN, √TN))`, each count's square root taken in
    doubles.
  - From −π to π; 0 when the two shares are equal; π when the decision equals the truth.
    It changes sign when the truth is complemented.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A decision with no 1 or no 0 is an error, as for the risk difference (ADR 0501).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and takes each arctangent of an exact square
    root in 50-digit decimals, by argument halving and the Taylor series.
  - The tolerance is `abs 1e-14, rel 1e-14`.
