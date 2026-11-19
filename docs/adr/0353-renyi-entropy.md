# ADR 0353: Rényi entropy

Status: accepted, 2026-11-18.

## Context

The Shannon entropy of a sample histogram is the simplest amplitude-domain complexity
measure. Rényi's family `H_α` contains it at `α = 1`. Its other members weight common
values (`α > 1`) or rare ones (`α < 1`) more, and `α = 0` counts the occupied bins. The bins
are ADR 0352's.

## Decision

- **The API.**
  - Python: `renyi_entropy(samples, alpha, bins=16)` in `measurements`, giving a float.
  - C#: `Measurements.RenyiEntropy(ReadOnlySpan<double> samples, double alpha,
    int bins = 16)`.
- **The value.**
  - The samples are binned as for auto mutual information (ADR 0352).
  - With `p_k` the share of samples in bin `k`, over the occupied bins:
    - `α = 0` gives `ln K`, where `K` is the number of occupied bins;
    - `α = 1` gives `−Σ p ln p`;
    - any other `α` gives `ln(Σ p^α)/(1 − α)`.
  - All are in nats.
- **The rules.**
  - `samples` real, one-dimensional and finite, and not all equal.
  - `alpha` finite and at least 0.
  - `bins` an integer from 2 to 4096.
- **Conditioning.** For `α` near 1 but not 1, `ln(Σ p^α)` and `1 − α` are both small, and
  the quotient loses about `−log10 |1 − α|` digits. The value is continuous there, but
  between the two languages it agrees only to that many fewer digits. There is no accurate
  `expm1` in .NET to avoid the loss with.

## Consequences

- **Vectors.**
  - The bins come from ADR 0352's exact rational binning, and the counts are exact.
  - `p^α` and the sums are taken in float.
  - The cases use `α` of 0, exactly 1, and values at least 0.5 away from 1.
  - The tolerance is `abs 1e-14, rel 1e-13`.
