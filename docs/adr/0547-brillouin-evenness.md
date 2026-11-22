# ADR 0547: The Brillouin evenness

Status: accepted, 2026-11-21.

## Context

The Brillouin index (ADR 0546) of `N` individuals in `k` kinds is largest when the counts
are as even as whole numbers allow: `k − r` kinds of `c` and `r` kinds of `c + 1`, with
`c = ⌊N/k⌋` and `r = N − ck`. The evenness is the index over that largest value.

## Decision

- **The API.**
  - Python: `brillouin_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.BrillouinEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = (ln N! − Σᵢ ln xᵢ!)/(ln N! − (k − r) ln c! − r ln (c + 1)!)`, `k` the number of
    values above 0; the common factor `1/N` cancels. Each `ln m!` is the sum of `ln j`,
    `j = 2 … m` in order, as for the index; `ln (c + 1)! = ln c! + ln(c + 1)`.
  - Above 0 and at most 1; 1 when the counts are as even as whole numbers allow. Zero
    values do not change it.
- **The rules.**
  - As for the Brillouin index, and with at least 2 values above 0, so the denominator
    is positive (fewer is `invalid_argument`).

## Consequences

- The same `O(N)` work as the index.
- **Vectors.**
  - The generator forms both multinomial coefficients exactly as integers and their
    logarithms in 50-digit `decimal`.
  - The tolerance is `abs 1e-13, rel 1e-12`, as for the index.
