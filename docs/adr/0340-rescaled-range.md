# ADR 0340: Rescaled range and the Hurst exponent

Status: accepted, 2026-11-18.

## Context

Hurst's rescaled-range analysis (1951), in the form Mandelbrot and Wallis gave it, is the
classic estimate of long-range dependence. It is reported next to DFA (ADR 0332), which is
more robust to trends but answers the same question. A series with no memory gives `H` near
0.5, a persistent one above it and an anti-persistent one below.

## Decision

- **The API.**
  - Python: `rescaled_range(samples, scales)` in `measurements`, giving the frozen dataclass
    `RescaledRange(scales, values, hurst)` (`eq=False`, as it holds arrays).
  - C#: `Measurements.RescaledRange(ReadOnlySpan<double> samples, ReadOnlySpan<int> scales)`,
    giving the record `RescaledRange(int[] Scales, double[] Values, double Hurst)`.
  - The name is the method's. `hurst` is the slope it leads to.
- **The value.** For scale `s`, the series is cut into `B = floor(N/s)` boxes from the start;
  the samples left at the end are not used. In each box:
  - `y_t = x_t − mean` for `t = 0 … s−1`, and `Z_t = Σ_{u≤t} y_u`. Note `Z_{s−1} = 0`.
  - `R = max_t Z_t − min_t Z_t`.
  - `S = sqrt(Σ y_t² / s)`, the population standard deviation.
  - The box gives `R/S`. The value at `s` is the mean of `R/S` over the boxes.
  - `hurst` is the least-squares slope of `ln(value)` against `ln s`.
  - There is no Anis-Lloyd small-sample correction. White noise therefore reads a little
    above 0.5 at short scales, as the raw method does.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `scales` integers, at least two of them, strictly increasing, each with `4 ≤ s ≤ N`.
  - Every box must have `S > 0`. A box that is constant is an error.

## Consequences

- **Vectors.**
  - The samples are dyadic. The generator takes each box's `R` and `S²` exactly in
    rationals. The square roots, the ratios, their mean (with `math.fsum`), the logarithms
    and the slope are taken in float.
  - The tolerance is `abs 1e-12, rel 1e-12`.
