# ADR 0199: Coherence significance threshold

Status: accepted, 2026-11-16. It goes with the coherence (ADR 0192).

## Context

An estimated coherence is never exactly 0, even between independent signals. The usual test
compares it with the level that independent Gaussian signals exceed with a small probability.
For `K` independent segments that level has a closed form, because the null distribution
satisfies `P(γ̂² > c) = (1 − c)^(K−1)`.

## Decision

- **The API.**
  - Python: `coherence_threshold(num_segments, alpha=0.05)` in `spectral`.
  - C#: `Spectral.CoherenceThreshold(int numSegments, double alpha = 0.05)`.
- **The definition.** The threshold is `1 − alpha^(1/(K−1))`, with `K = num_segments`.
- **The rules.**
  - `K` is an integer of at least 2.
  - `alpha` is finite and strictly between 0 and 1.
  - Anything else is `invalid_argument`.
- **Overlap.** Overlapped segments are not independent, so they are worth fewer than `K`. The
  function uses the `K` it is given. A caller using 50 % Hann overlap who wants a conservative
  test passes a smaller effective count. The docs say this; the function does not guess it.

## Consequences

- **Vectors.** They are closed forms:
  - `K = 2, alpha = 0.05` gives `0.95`;
  - `K = 3, alpha = 0.01` gives `0.9`;
  - `K = 5, alpha = 0.5` gives `1 − 2^(−1/4)`;
  - `K = 11, alpha = 0.05` gives `1 − 0.05^0.1`.

  They also cover the argument errors.
- **A unit test** checks the false-alarm rate on independent noise, in Python.
