# ADR 0341: Dispersion entropy

Status: accepted, 2026-11-18.

## Context

Permutation entropy (ADR 0325) keeps only the order of the samples in a window. Rostaghi and
Azami (2016) proposed dispersion entropy, which keeps their sizes too, coarsely. It is fast,
like permutation entropy, and is used on biomedical and machine-vibration signals.

## Decision

- **The API.**
  - Python: `dispersion_entropy(samples, m, classes, delay=1)` in `measurements`, giving a
    float.
  - C#: `Measurements.DispersionEntropy(ReadOnlySpan<double> samples, int m, int classes,
    int delay = 1)`.
- **The value.** With `N` samples, `c` classes and `μ` and `σ` the mean and the population
  standard deviation of the samples:
  - `y_i = Φ((x_i − μ)/σ) = erfc(−(x_i − μ)/(σ√2))/2`.
  - The class is `z_i = min(c, floor(c·y_i) + 1)`, from 1 to `c`. The paper writes
    `round(c·y_i + 0.5)`, which is the same except where `c·y_i` is an integer. There the
    floor form is the one that keeps every class the same width, and it has no tie rule to
    differ between languages.
  - The `N − (m − 1)·delay` patterns are `(z_i, z_{i+delay}, …, z_{i+(m−1)·delay})`.
  - The value is `−Σ p·ln p / ln(cᵐ)` over the patterns that occur, from 0 to 1.
- **The rules.**
  - `samples` real, one-dimensional, finite and not constant.
  - `m` an integer from 1 to 10. `classes` an integer from 2 to 64, so a pattern fits in 60
    bits. `delay` an integer of at least 1.
  - At least one pattern: `N ≥ (m − 1)·delay + 1`.

## Consequences

- **Vectors.**
  - The generator takes `μ` and `σ²` exactly in rationals and `Φ` with `math.erfc`. It
    asserts that every `c·y_i` is at least `1e-9` from an integer, so no class can differ
    between languages. The counts are then exact, and the entropy is taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
