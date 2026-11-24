# ADR 0605: Vanderploeg and Scavia's relativized electivity

Status: accepted, 2026-11-23.

## Context

Vanderploeg and Scavia (1979) put Manly's alpha on Ivlev's scale. With `α_i` Manly's alpha
for kind `i` of `n` (ADR 0602), `E*_i = (α_i − 1/n)/(α_i + 1/n)`. It is −1 for a kind that is
not used, 0 for a kind used as it is available, and approaches 1 for a kind strongly
preferred. Unlike Ivlev's electivity it compares preferences rather than shares, so it does
not depend on how abundant each kind is.

## Decision

- **The API.**
  - Python: `vanderploeg_scavia_electivity(x, available)` in `measurements`, giving an
    array of floats.
  - C#: `Measurements.VanderploegScaviaElectivity(ReadOnlySpan<double> x,
    ReadOnlySpan<double> available)`, giving `double[]`.
- **The form.** `α` is computed by `manly_alpha`, with its rules and its order of
  operations. Then, with `e = 1/n`, each value is `(α_i − e)/(α_i + e)`, held to −1 to 1.
- **The rules.** As for `manly_alpha`, which does the checking: the records one-dimensional,
  real, finite, at least 0, not empty, with a value above 0, the same length; `available`
  above 0 everywhere; an availability share that underflows to 0, or a sum of ratios that
  overflows, refused. Otherwise `invalid_argument`.

## Consequences

- **Vectors.**
  - The generator forms Manly's alpha and the values with fractions.
  - The tolerance is `abs 1e-14, rel 1e-14`, for the rounding of the sums.
