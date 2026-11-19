# ADR 0350: Recurrence quantification

Status: accepted, 2026-11-18.

## Context

A recurrence plot marks every pair of times at which an embedded trajectory comes back close
to itself. Zbilut and Webber's recurrence quantification analysis reduces it to a few
numbers. The three most used are the recurrence rate, the determinism (the share of
recurrent points on diagonal lines, which a deterministic system makes and noise mostly does
not), and the longest diagonal line.

## Decision

- **The API.**
  - Python: `recurrence_quantification(samples, m, radius, delay=1, min_line=2,
    theiler=0)` in `measurements`, giving a frozen dataclass
    `RecurrenceQuantification(rate, determinism, longest)`.
  - C#: `Measurements.RecurrenceQuantification(ReadOnlySpan<double> samples, int m,
    double radius, int delay = 1, int minLine = 2, int theiler = 0)`, giving the record
    `RecurrenceQuantification(double Rate, double Determinism, int Longest)`.
- **The plot.**
  - The vectors are embedded as for the correlation sum (ADR 0349), `W = N − (m − 1)τ` of
    them.
  - `R_ij = 1` when the Chebyshev distance between `v_i` and `v_j` is **strictly** below
    `radius`.
  - Only the points with `j − i > w` count, where `w` is the Theiler window. The plot is
    symmetric, so the upper triangle gives the same shares as the whole plot without the
    band `|i − j| ≤ w`. That band always holds the line of identity, which is left out.
- **The values.**
  - `rate` is the number of recurrent points over the number of points with `j − i > w`.
  - A diagonal line is a maximal run of recurrent points along one diagonal `j − i = s`.
  - `determinism` is the number of recurrent points on lines of at least `min_line`
    points, over the number of recurrent points.
  - `longest` is the length of the longest line, or 0 if there are none.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `m`, `delay` and `min_line` integers of at least 1, and `theiler` of at least 0.
  - `radius` finite and positive.
  - There must be at least one point with `j − i > w`.
  - There must be at least one recurrent point, or `determinism` is undefined; that is an
    error.

## Consequences

- **Vectors.**
  - The samples and radius are dyadic, so every distance and comparison is exact. The
    generator builds the plot in rationals and counts the runs exactly.
  - The values are ratios of integers.
  - The tolerance is `abs 1e-15, rel 1e-15`.
