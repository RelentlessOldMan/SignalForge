# ADR 0534: The Smith–Wilson evenness

Status: accepted, 2026-11-21.

## Context

Smith and Wilson (1996) give `E_var`, an evenness from the variance of the logarithms of
the values, mapped onto 0 to 1 by the arctangent. It needs every value above 0. Texts
differ on the variance divisor; here it is `n`, as in the original.

## Decision

- **The API.**
  - Python: `smith_wilson_evenness(samples)` in `measurements`, giving a float.
  - C#: `Measurements.SmithWilsonEvenness(ReadOnlySpan<double> samples)`.
- **The value.**
  - `E = 1 − (2/π)·arctan(V)`, `V = Σᵢ (ln xᵢ − m)²/n`, `m = Σᵢ ln xᵢ / n`; both sums in
    record order. Formed as `1 − (2/π)·atan(V)`, `2/π` divided first.
  - 1 when every value is equal (or there is one value), falling toward 0 as the values
    spread. Unchanged when every value is scaled by the same positive factor, so it does
    not need the shares.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value above 0.

## Consequences

- Two passes over the logarithms; no sort.
- **Vectors.**
  - The generator forms the logarithms, the variance and the arctangent in 50-digit
    `decimal`: the arctangent by halving the argument and its Taylor series, and π by
    Machin's formula.
  - The tolerance is `abs 1e-14, rel 1e-13`, for `log` and `atan` in each language.
