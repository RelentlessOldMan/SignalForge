# ADR 0351: Fisher information

Status: accepted, 2026-11-18.

## Context

SVD entropy (ADR 0342) reads the spread of the singular spectrum of the delay embedding.
Roberts, Penny and Rezek (1999) read the same spectrum another way, through a discrete
Fisher information, which is large when the spectrum falls steeply and 0 when it is flat.
It reuses ADR 0342's embedding and singular values.

## Decision

- **The API.**
  - Python: `fisher_information(samples, order, delay=1)` in `measurements`, giving a
    float.
  - C#: `Measurements.FisherInformation(ReadOnlySpan<double> samples, int order,
    int delay = 1)`.
- **The value.**
  - The embedding matrix and its singular values are as for SVD entropy (ADR 0342).
  - The singular values are sorted from largest to smallest and divided by their sum,
    giving `σ̄_1 ≥ … ≥ σ̄_m`.
  - The value is `Σ_{i=1}^{m−1} (σ̄_{i+1} − σ̄_i)² / σ̄_i`.
  - A term with `σ̄_i = 0` is 0, since every later `σ̄` is 0 too. That is also its limit,
    so a value that is tiny in one language and exactly 0 in the other changes nothing.
- **The rules.** The same as for SVD entropy: `samples` real, one-dimensional, finite and not
  all 0; `order` from 2 to 32; `delay` at least 1; at least `order` rows.

## Consequences

- **Vectors.**
  - As in ADR 0342, the generator forms the Gram matrix `AᵀA` exactly in rationals and takes
    its eigenvalues by a closed form at order 2 or by float Jacobi above that. These are
    independent of either language's SVD.
  - The singular values are the square roots, sorted.
  - The tolerance is ADR 0342's, `abs 1e-12, rel 1e-11`.
