# ADR 0517: The Lorenz curve

Status: accepted, 2026-11-20.

## Context

The Lorenz curve plots the share of a total held by the smallest `k` of `n` holders
against `k/n`. The inequality measures of ADRs 0510–0516 summarize it: the Gini
coefficient is twice the area between it and the line of equality, and the Hoover index
is its largest gap below that line.

## Decision

- **The API.**
  - Python: `lorenz_curve(samples)` in `measurements`, giving an array of `n + 1` floats.
  - C#: `Measurements.LorenzCurve(ReadOnlySpan<double> samples)`, giving a `double[]`.
- **The value.**
  - `L₀ = 0` and `Lₖ = Sₖ/Sₙ`, `Sₖ` the running sum of the `k` smallest values, added
    one by one from the smallest; the point `k` sits at `k/n`. Only the shares are
    returned.
  - Dividing by the running sum `Sₙ`, not a separate total, makes the last share exactly
    1 and both languages agree to the bit. The shares never fall, and `Lₖ ≤ k/n`.
- **The rules.**
  - A real, finite, one-dimensional record of at least 1 value, every value at least 0,
    not all 0, as for the Gini coefficient.

## Consequences

- The cost is a sort.
- **Vectors.**
  - The generator sorts dyadic values and forms each running share exactly in rationals.
  - The tolerance is `abs 1e-15, rel 1e-14`.
