# ADR 0346: Attention entropy

Status: accepted, 2026-11-18.

## Context

Yang, Wang, Peng and others (2020) proposed attention entropy. It ignores most samples and
looks only at where the local peaks and troughs fall, which makes it fast and usable on short
records. The value is the entropy of the gaps between those key points.

## Decision

- **The API.**
  - Python: `attention_entropy(samples)` in `measurements`, giving a float.
  - C#: `Measurements.AttentionEntropy(ReadOnlySpan<double> samples)`.
- **The key points.**
  - A local maximum is an index `0 < i < N−1` with `x_i > x_{i−1}` and `x_i > x_{i+1}`.
    A local minimum is the same with `<`.
  - The comparisons are strict, so a sample on a plateau is neither. The first and last
    samples are never key points.
- **The intervals.** There are four sets of intervals, in samples:
  - max to max: the gaps between successive maxima.
  - min to min: the gaps between successive minima.
  - max to min: from each maximum to the first minimum after it, where there is one.
  - min to max: from each minimum to the first maximum after it, where there is one.
- **The value.**
  - Each set gives the Shannon entropy in nats, `−Σ p·ln p`, of how often each interval
    length occurs.
  - The value is the mean of the four.
  - Published code uses base 2 and pairs the cross intervals in slightly different ways.
    This ADR fixes the definition above, and the value is in nats. Dividing by `ln 2` gives
    bits.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - Each of the four sets must have at least one interval, or the value is undefined.

## Consequences

- **Vectors.**
  - The generator finds the key points and intervals with plain loops and counts them
    exactly. The logarithms are taken in float.
  - The tolerance is `abs 1e-14, rel 1e-13`.
