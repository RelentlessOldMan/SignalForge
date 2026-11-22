# ADR 0550: Fisher's alpha

Status: accepted, 2026-11-21.

## Context

Fisher, Corbet and Williams (1943) fit a log-series to counts of kinds. Its one parameter
`α` ties the number of kinds `k` to the number of individuals `N` by `k = α ln(1 + N/α)`.
There is no closed form for `α`; it has to be solved for.

## Decision

- **The API.**
  - Python: `fisher_alpha(samples)` in `measurements`, giving a float.
  - C#: `Measurements.FisherAlpha(ReadOnlySpan<double> samples)`.
- **The value.**
  - The `α > 0` with `α ln(1 + N/α) = k`, `k` the number of values above 0 and `N = Σᵢ xᵢ`
    added in record order. The left side rises from 0 to `N` as `α` grows, so the root is
    unique when `0 < k < N`.
  - The left side is `f(α) = α · lp(N/α)`, with `lp(x)` the accurate `ln(1 + x)`: with
    `u = 1 + x`, `x` when `u = 1`, else `ln(u) · x/(u − 1)`, formed left to right. Plain
    `ln(1 + x)` loses the digits that matter when `α` is large.
- **The search.** In both languages, step for step:
  - `lo` starts at 1 and halves while `f(lo) ≥ k`; `hi` starts at 1 and doubles while
    `f(hi) ≤ k`.
  - Then 100 steps of `mid = √lo · √hi`: `lo = mid` when `f(mid) < k`, else `hi = mid`.
  - The value is `√lo · √hi` after the last step.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.
  - The total above `k`, so some value is above 1 (otherwise `invalid_argument`). Whole
    numbers give `N − k ≥ 1`, so `hi` stays below `2N²`.

## Consequences

- The bracket is found in about `2 log₂ N` steps, then a fixed 100; the bracket is far
  narrower than one unit in the last place well before the end.
- **Vectors.**
  - The generator solves for `α` by bisection in 50-digit decimal, on `ln(1 + N/α)` as a
    decimal logarithm, independent of the float search.
  - The tolerance is `abs 1e-13, rel 1e-12`: `α` is about `N` times as sensitive as `k`
    when `k` is near `N`.
