# ADR 0358: Cosine similarity entropy

Status: accepted, 2026-11-18.

## Context

Chanwimalueang and Mandic (2017) proposed cosine similarity entropy. It is like sample entropy,
but it compares embedded vectors by the angle between them, not their distance, so it ignores
amplitude. The value is the binary Shannon entropy of the share of vector pairs that are
similar.

## Decision

- **The API.**
  - Python: `cosine_similarity_entropy(samples, m, r, delay=1)` in `measurements`, giving a
    float.
  - C#: `Measurements.CosineSimilarityEntropy(ReadOnlySpan<double> samples, int m, double r,
    int delay = 1)`.
- **The value.**
  - The vectors are `v_i = (x_i, x_{i+τ}, …, x_{i+(m−1)τ})` for `i = 0 … W − 1`, with
    `W = N − (m − 1)τ`.
  - The angular distance of two vectors is `arccos(c)/π`, where `c` is their cosine
    similarity clipped to `[−1, 1]`. It runs from 0 (same direction) to 1 (opposite).
  - `B` is the share of the `W(W − 1)/2` pairs `i < j` whose angular distance is strictly
    below `r`.
  - The value is `−B log2 B − (1 − B) log2(1 − B)`, in bits, with `0 log 0 = 0`.
  - The paper normalizes the record to zero mean or median first. SignalForge does not; a
    caller who wants it subtracts the mean first.
- **The rules.**
  - `samples` real, one-dimensional and finite.
  - `m` and `delay` integers, at least 1.
  - `W ≥ 2`.
  - `r` finite, with `0 < r ≤ 1`.
  - No embedded vector may be all zeros, since its angle is undefined.

## Consequences

- **Vectors.**
  - The generator computes each angle in float and asserts that it is at least `1e-9` from
    `r`, so the counts are exact in both languages.
  - The entropy is then taken in float. The tolerance is `abs 1e-14, rel 1e-13`.
