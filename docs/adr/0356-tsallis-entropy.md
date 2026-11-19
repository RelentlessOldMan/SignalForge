# ADR 0356: Tsallis entropy

Status: accepted, 2026-11-18.

## Context

Tsallis's entropy is the other common one-parameter family around Shannon's, next to Rényi's
(ADR 0353). It is not additive over independent parts, and it is widely used on biomedical
histograms. It uses the same bins.

## Decision

- **The API.**
  - Python: `tsallis_entropy(samples, q, bins=16)` in `measurements`, giving a float.
  - C#: `Measurements.TsallisEntropy(ReadOnlySpan<double> samples, double q,
    int bins = 16)`.
- **The value.**
  - The samples are binned as for auto mutual information (ADR 0352).
  - With `p_k` the share of samples in bin `k`, over the occupied bins:
    - `q = 1` gives `−Σ p ln p`;
    - any other `q` gives `(1 − Σ p^q)/(q − 1)`.
  - At `q = 0` this is `K − 1`, where `K` is the number of occupied bins.
- **The rules.**
  - `samples` real, one-dimensional and finite, and not all equal.
  - `q` finite and at least 0.
  - `bins` an integer from 2 to 4096.
- **Conditioning.** As for Rényi entropy, for `q` near 1 but not 1 the quotient loses about
  `−log10 |1 − q|` digits.

## Consequences

- **Vectors.**
  - The bins and counts are exact, as in ADR 0353, and `p^q` and the sums are taken in
    float.
  - The cases use `q` of 0, exactly 1, and values at least 0.5 away from 1.
  - The tolerance is `abs 1e-14, rel 1e-13`.
