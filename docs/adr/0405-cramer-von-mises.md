# ADR 0405: The two-sample Cramér–von Mises statistic

Status: accepted, 2026-11-19.

## Context

Between the largest gap of Kolmogorov–Smirnov (ADR 0402) and the area of the Wasserstein
distance (ADR 0403), the Cramér–von Mises criterion averages the squared gap between the two
empirical distribution functions over the pooled sample. It does not depend on the units of
the data, only on the order of the values.

## Decision

- **The API.**
  - Python: `cramer_von_mises(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.CramerVonMises(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - The statistic only; no p-value.
- **The value.**
  - `T = n_x·n_y/N² · Σ_k (F_x(z_k) − F_y(z_k))²` over all `N = n_x + n_y` pooled values
    `z_k`, each counted as often as it occurs; `F_x(t) = #(xᵢ ≤ t)/n_x`. This is Anderson's
    (1962) form; with ties each tied value takes the distribution functions just after the tie.
  - At each distinct pooled value `t`, with `c` copies, the whole number
    `g = |#(x ≤ t)·n_y − #(y ≤ t)·n_x|` gives `c·g²` in `double` (`c`, then `g·g`, each a
    `double` product). The terms are summed in increasing `t`, then divided once by
    `n_x·n_y·N²`, that product in `double`.
  - Symmetric; zero when both samples hold the same values in the same proportions.
- **The rules.**
  - Each sample one-dimensional, real and finite, at least 1.

## Consequences

- The cost is a sort of each sample and a merge.
- **Vectors.**
  - The generator forms the sum over every pooled value exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-13`.
