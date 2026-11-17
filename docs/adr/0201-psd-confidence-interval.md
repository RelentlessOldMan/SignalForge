# ADR 0201: PSD confidence interval

Status: accepted, 2026-11-16. It goes with the Welch degrees of freedom (ADR 0200).

## Context

A Welch PSD bin with `ν` equivalent degrees of freedom is distributed as `P·χ²_ν/ν` about the
true density `P`. A two-sided interval at level `c` therefore needs two chi-squared quantiles,
for real `ν` (Welch's `ν` is not an integer). Neither language has one in its allowed
dependencies: NumPy has none, and .NET has no log-gamma.

## Decision

- **The API.**
  - Python: `psd_confidence_interval(psd, dof, confidence=0.95)` in `spectral`.
  - C#: `Spectral.PsdConfidenceInterval(ReadOnlySpan<double> psd, double dof, double
    confidence = 0.95)`.
  - Both return `PsdConfidenceInterval(lower, upper)`, two arrays of the length of `psd`.
- **The definition.**
  - `lower = ν·P / q_ν((1 + c)/2)` and `upper = ν·P / q_ν((1 − c)/2)`.
  - `q_ν(p)` is the chi-squared quantile.
  - A zero bin gives `[0, 0]`.
- **The quantile.** It is private: a helper, not a public API.
  - `q_ν(p) = 2y`, where `y` solves `P(ν/2, y) = p`.
  - `P` and `Q` are the regularized incomplete gammas. They come from the power series for
    `x < a + 1`, and otherwise from the continued fraction for `Q`, evaluated with Lentz's
    method.
  - For `p > ½` it solves `Q = 1 − p` instead, which keeps the upper tail accurate.
  - The root is bracketed by doubling, then refined by Newton steps that fall back to bisection
    when they leave the bracket.
- **Log-gamma.**
  - Python uses `math.lgamma`.
  - C# shifts the argument up to at least 15 with `Γ(x+1) = x·Γ(x)`, then uses Stirling's series
    through the `B₁₄` term. Its error is below 1e-15 there.
- **The accuracy target.** A relative error of 1e-12 for `ν` in [0.5, 10⁴] and
  `p` in [1e-6, 1 − 1e-6].
- **The rules.**
  - `psd` is one-dimensional, finite and non-negative.
  - `dof` is finite and positive.
  - `confidence` is strictly between 0 and 1.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** Their expected quantiles come from closed-form chi-squared CDFs, solved by stdlib
  bisection:
  - `ν = 2` gives `−2 ln(1 − p)` exactly;
  - `ν = 1` uses `erf(√(x/2))`;
  - `ν = 3` uses `erf(√(x/2)) − √(2x/π)·e^(−x/2)`;
  - `ν = 4` uses `1 − e^(−x/2)(1 + x/2)`.

  One non-integer case, `ν = 7.5`, uses a stdlib series for `P` with `math.lgamma`, written
  separately in the generator.
- **The C# log-gamma** is checked through these vectors. The two languages agree to the vector
  tolerance.
