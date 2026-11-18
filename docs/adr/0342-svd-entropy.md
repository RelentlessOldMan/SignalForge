# ADR 0342: SVD entropy

Status: accepted, 2026-11-18.

## Context

SVD entropy (Roberts, Penny and Rezek, 1999) measures how many independent directions a
delay embedding of a signal needs. A sine fills two, noise fills all of them. It is one of the
standard complexity features, next to permutation entropy (ADR 0325).

## Decision

- **The API.**
  - Python: `svd_entropy(samples, order, delay=1)` in `measurements`, giving a float.
  - C#: `Measurements.SvdEntropy(ReadOnlySpan<double> samples, int order, int delay = 1)`.
- **The value.**
  - With `N` samples, the embedding matrix has `K = N − (order − 1)·delay` rows. Row `i` is
    `(x_i, x_{i+delay}, …, x_{i+(order−1)·delay})`. The mean is not removed.
  - `σ_1 … σ_order` are its singular values, and `p_k = σ_k / Σ σ`.
  - The value is `−Σ p_k·ln p_k / ln(order)` over the `p_k > 0`, from 0 to 1.
  - Some sources use the squared singular values, or leave the value unnormalized. This ADR
    uses the singular values themselves, normalized, as Roberts et al. did.
- **How.**
  - Python takes the singular values with `numpy.linalg.svd`.
  - C# has no linear algebra in its base library, so it uses the one-sided Jacobi method of
    Hestenes: rotate pairs of columns until all are orthogonal, then the singular values are
    the column norms. It works on the matrix itself, not on `AᵀA`, so small singular values
    keep their relative accuracy.
- **The rules.**
  - `samples` real, one-dimensional, finite and not all 0.
  - `order` an integer from 2 to 32. `delay` an integer of at least 1.
  - `K ≥ order`.

## Consequences

- **Vectors.**
  - The generator forms `AᵀA` exactly in rationals. For order 2 it takes the eigenvalues in
    closed form, the smaller as the determinant over the larger. For higher orders it uses
    the cyclic Jacobi eigenvalue method in float. The square roots and the entropy are taken
    in float.
  - Every vector has full rank, with `λ_min/λ_max > 1e-6` asserted. Rounding in `AᵀA` cannot
    move a singular value further than the tolerance allows.
  - The tolerance is `abs 1e-12, rel 1e-11`.
