# ADR 0393: The ROC AUC

Status: accepted, 2026-11-19.

## Context

The area under the receiver operating characteristic grades a real-valued score, not a
decision: it is the probability that a random positive scores higher than a random negative
(Hanley and McNeil, 1982), which is the Mann–Whitney U over the product of the class sizes.

## Decision

- **The API.**
  - Python: `roc_auc(truth, score)` in `measurements`, giving a float.
  - C#: `Measurements.RocAuc(ReadOnlySpan<double> truth, ReadOnlySpan<double> score)`.
  - `truth` holds 0 and 1, 1 positive; a higher `score` means more likely positive.
- **The value.**
  - `AUC = (R₁ − n₁(n₁ + 1)/2)/(n₁·n₀)`, `R₁` the sum of the positives' ranks among all scores,
    tied scores given their mean rank. So a tied positive–negative pair counts one half: the
    area under the ROC curve drawn with straight segments through tied thresholds.
  - The mean ranks are multiples of 1/2, so `R₁` and the numerator are exact while `N` is
    below `2²⁶`; one division gives the correctly rounded share.
  - From 0 to 1; 1/2 for a score no better than chance.
- **The rules.**
  - Both records one-dimensional, the same length.
  - Every truth 0 or 1; every score finite.
  - At least one positive and one negative.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator counts every positive–negative pair in integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
