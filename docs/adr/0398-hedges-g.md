# ADR 0398: Hedges' g

Status: accepted, 2026-11-19.

## Context

Cohen's d (ADR 0397) overstates the population effect in small samples. Hedges (1981) gave
the factor that makes it unbiased under normality, `J(m) = Γ(m/2)/(√(m/2)·Γ((m − 1)/2))` with
`m` the degrees of freedom of the pooled variance. The common approximation
`1 − 3/(4m − 1)` is not used: the exact factor costs no more here.

## Decision

- **The API.**
  - Python: `hedges_g(x, y)` in `measurements`, giving a float.
  - C#: `Measurements.HedgesG(ReadOnlySpan<double> x, ReadOnlySpan<double> y)`.
  - The arguments, the sign and the rules as for Cohen's d.
- **The value.**
  - `g = J(m)·d`, `m = n_x + n_y − 2`, `d` exactly as Cohen's d computes it.
  - `J(m) = exp(ln Γ(m/2) − ln Γ((m − 1)/2))/√(m/2)`, the log-gamma from `math.lgamma` in
    Python and the library's own (ADR 0201) in C#. The difference of two log-gammas loses
    about `log₂ m` bits, so `J` is good to about `m·2⁻⁵³` relative; at `m = 100` that is
    about `1e-14`.
  - `J(2) = 1/√π`; `J` rises towards 1 as `m` grows.

## Consequences

- The cost is that of Cohen's d.
- **Vectors.**
  - The generator forms `J` exactly from factorials and `√π` (π to 50 digits), and `d` as the
    Cohen's d generator does, in 40-digit decimal.
  - The tolerance is `abs 1e-15, rel 1e-12`, for the log-gamma difference.
