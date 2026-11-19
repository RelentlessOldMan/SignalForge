# ADR 0361: Runs test

Status: accepted, 2026-11-18.

## Context

The Wald–Wolfowitz runs test asks whether a record is random. It labels each sample as above
or below a central value and counts the runs of equal labels. Too few runs means trends or
clustering, and too many means alternation. It is distribution-free, like the turning point
test (ADR 0360).

## Decision

- **The API.**
  - Python: `runs_test(samples)` in `measurements`, giving a frozen dataclass
    `RunsTest(runs, z)`.
  - C#: `Measurements.RunsTest(ReadOnlySpan<double> samples)`, giving the record
    `RunsTest(int Runs, double Z)`.
- **The value.**
  - The central value is the mean, computed in float as the sum divided by `N`.
  - Samples above it are labelled +, samples below it −, and samples equal to it are
    dropped.
  - `n₁` and `n₂` are the numbers of + and − labels, and `n = n₁ + n₂`.
  - `runs` is the number of maximal blocks of equal labels in the labels left.
  - `μ = 2n₁n₂/n + 1` and `σ² = 2n₁n₂(2n₁n₂ − n)/(n²(n − 1))`.
  - `z = (runs − μ)/σ`.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `σ² > 0`, which needs both labels and `2n₁n₂ > n`.

## Consequences

- **Vectors.**
  - The labels depend on comparisons with a float mean. So the vector samples are dyadic, with
    an exact float sum, and the generator asserts that the float mean equals the exact one.
  - `μ` and `σ²` are rational. The square root and the quotient are taken in float.
  - The tolerance on `z` is `abs 1e-14, rel 1e-13`.
