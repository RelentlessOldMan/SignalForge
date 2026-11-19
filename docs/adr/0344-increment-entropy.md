# ADR 0344: Increment entropy

Status: accepted, 2026-11-18.

## Context

Increment entropy (Liu, Wei, Cheng et al., 2016) describes a signal by its steps rather than
its values. Each step becomes a letter made of its direction and a coarse size, and the
measure is the entropy of words of consecutive letters. It responds to both the order and
the size of changes, and it is cheap.

## Decision

- **The API.**
  - Python: `increment_entropy(samples, m, levels)` in `measurements`, giving a float.
  - C#: `Measurements.IncrementEntropy(ReadOnlySpan<double> samples, int m, int levels)`.
- **The value.**
  - The increments are `v_i = x_{i+1} − x_i`, `N − 1` of them. `σ` is their population
    standard deviation.
  - Each increment becomes the letter `(sign v_i, min(R, floor(|v_i|·R/σ)))`, with
    `R = levels`.
  - The words are the `N − m` runs of `m` consecutive letters.
  - The value is the Shannon entropy of the words in nats, `−Σ p·ln p`.
- **Choices this ADR makes.** Published versions differ in the details, so these are
  ours:
  - `σ` is the population deviation, not the sample one.
  - The value is not normalized. Some tools divide by `m − 1`, and some use base 2; either
    is a single line for the caller.
- **The rules.**
  - `samples` real, one-dimensional and finite, at least `m + 1` of them.
  - The increments must not all be 0.
  - `m` an integer of at least 1. `levels` an integer from 1 to 1000.

## Consequences

- **Vectors.**
  - The generator takes `σ²` exactly in rationals and each size exactly: the largest `k`
    with `k²·σ² ≤ v²·R²`. It asserts that no nonzero `|v|·R/σ` below `R` is an integer
    or within `1e-9` of one, so the float floor in the libraries cannot differ. The counts are exact, and the
    entropy is taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
