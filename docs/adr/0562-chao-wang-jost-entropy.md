# ADR 0562: The Chao–Wang–Jost entropy

Status: accepted, 2026-11-21.

## Context

Chao, Wang and Jost (2013) estimate the Shannon entropy of counts in two parts: the kinds
seen, through Zhang's series in closed form, and the kinds not seen, through the
singletons and doubletons:
`H = Σ_{1≤xᵢ≤N−1} (xᵢ/N)(h(N − 1) − h(xᵢ − 1)) + (F₁/N)(1 − A)^{1−N}(−ln A − Σ_{r=1}^{N−1} (1 − A)^r/r)`,
`h` the harmonic numbers and `A = 2F₂/((N − 1)F₁ + 2F₂)`, or `2/((N − 1)(F₁ − 1) + 2)`
with no doubletons, or 1 with no singletons.

## Decision

- **The API.**
  - Python: `chao_wang_jost_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.ChaoWangJostEntropy(ReadOnlySpan<double> samples)`.
- **The first part.**
  - `h(m)` over ascending `j` up to `N − 1`, keeping `h(xᵢ − 1)` on the way.
  - `Σ (xᵢ/N)(h(N − 1) − h(xᵢ − 1))` over values from 1 to `N − 1` in record order.
- **The second part, 0 with no singletons.**
  - Since `−ln A = Σ_{r≥1} (1 − A)^r/r`, the bracket times `(1 − A)^{1−N}` is
    `B = q Σ_{m≥0} qᵐ/(N + m)`, `q = 1 − A`. The closed form subtracts nearly equal
    numbers and multiplies by a large power when `A·N` is large, so:
  - When `A·N ≥ 1`, the tail form: `w = 1`, then for `m = 0, 1, …` add `w/(N + m)` and
    set `w ← w·q`, stopping at the first term that leaves the sum unchanged; `B = q` times
    the sum. It takes about `37/A ≤ 37N` steps. `A = 1` gives `B = 0`.
  - When `A·N < 1`, the closed form: `w ← w·q` and the sum of `w/r` for `r = 1, …, N − 1`,
    and `B = q^{1−N}(−ln A − that sum)`; the cancellation then costs at most about two
    digits.
  - `H = first part + (F₁/N)·B`; 0 when one value holds the total.
- **The rules.**
  - Whole numbers, as for Zhang's entropy: totalling more than 1 and at most 10 000
    (otherwise `invalid_argument`).

## Consequences

- **Vectors.**
  - The generator evaluates the paper's closed form in 60-digit decimal, which needs no
    switch.
  - The tolerance is `abs 1e-12, rel 1e-11`.
