# ADR 0559: The Grassberger entropy

Status: accepted, 2026-11-21.

## Context

Grassberger (2003) estimates the Shannon entropy of counts as
`H = ln N − (1/N) Σᵢ xᵢ G(xᵢ)` with `G(n) = ψ(n) + ½(−1)ⁿ(ψ((n + 1)/2) − ψ(n/2))`, ψ the
digamma function. At whole numbers it satisfies `G(1) = −γ − ln 2`, `G(2) = 2 − γ − ln 2`,
`G(2m + 1) = G(2m)` and `G(2m + 2) = G(2m) + 2/(2m + 1)`, so
`G(n) = O(⌊n/2⌋) − γ − ln 2` with `O(m) = Σ_{j=0}^{m−1} 2/(2j + 1)`.

## Decision

- **The API.**
  - Python: `grassberger_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.GrassbergerEntropy(ReadOnlySpan<double> samples)`.
- **The value.**
  - For each value above 0, in record order, `O(⌊xᵢ/2⌋)` summed over ascending `j`, and
    `A = Σ xᵢ O(⌊xᵢ/2⌋)`.
  - `H = ln N + γ + ln 2 − A/N`, left to right, with `γ` the double nearest Euler's
    constant, `0.5772156649015329`.
  - Not 0 for one kind (`[4]` gives `3 ln 2 + γ − 8/3`, a little below 0): the estimate
    corrects for kinds not seen.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.

## Consequences

- The inner sums take `N/2` steps in all, at most 5 000 000.
- **Vectors.**
  - The generator forms `G` from the digamma definition (ψ at whole numbers from the
    harmonic numbers, at half-whole numbers from `ψ(½) = −γ − 2 ln 2` and the step
    `ψ(z + 1) = ψ(z) + 1/z`), in 50-digit decimal with `γ` to 50 digits.
  - The tolerance is `abs 1e-12, rel 1e-12`.
