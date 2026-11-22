# ADR 0570: The Sharma–Mittal diversity of counts

Status: accepted, 2026-11-22.

## Context

Sharma and Mittal (1975) join the Rényi and Tsallis entropies in one family of order `q`
and degree `r`: `((Σ pᵢ^q)^{(1−r)/(1−q)} − 1)/(1 − r)`. It is the Rényi entropy at `r = 1`,
the Tsallis entropy at `r = q`, and `D_q − 1`, the Hill number less one, at `r = 0`.

## Decision

- **The API.**
  - Python: `sharma_mittal_diversity(samples, order, degree)` in `measurements`, giving a
    float.
  - C#: `Measurements.SharmaMittalDiversity(ReadOnlySpan<double> samples, double order,
    double degree)`.
- **The form.** With `R` the Rényi diversity of counts of order `q` (ADR 0566, with its
  switches), the value is `R` at `r = 1`, else `expm1((1 − r) R)/(1 − r)`. This keeps its
  digits when `r` is near 1.
- **The rules.** As for the Hill number: records as for the Gini coefficient, `order`
  finite and at least 0; `degree` finite. Otherwise `invalid_argument`. A result too large
  for a double comes out as infinity in C#; Python raises the `OverflowError` of
  `math.expm1`. The vectors stay well inside the range.

## Consequences

- **Vectors.**
  - The generator takes exact shares and evaluates
    `((Σ pᵢ^q)^{(1−r)/(1−q)} − 1)/(1 − r)`, with the Shannon entropy in place of the
    Rényi entropy at `q = 1` and the Rényi entropy itself at `r = 1`, in 60-digit decimal.
  - The tolerance is `abs 1e-12, rel 1e-12`.
