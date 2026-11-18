# ADR 0336: Lempel-Ziv complexity

Status: accepted, 2026-11-18.

## Context

The Lempel-Ziv complexity (Lempel and Ziv, 1976) counts how many new phrases a left-to-right
parse of a sequence produces, each phrase being the shortest piece that cannot be copied from
what came before. It is a model-free measure of how much new pattern a binary sequence holds.
It is used on binarized EEG and on bit streams. Kaspar and Schuster (1987) gave the usual
linear-scan algorithm.

## Decision

- **The API.**
  - Python: `lempel_ziv_complexity(bits)` in `measurements`, giving an int.
  - C#: `Measurements.LempelZivComplexity(ReadOnlySpan<byte> bits)`, giving an `int`.
- **The value.** For a sequence `s` of `n` bits, the parse starts at `p = 0`.
  - Each phrase is `s[p … q]` for the smallest `q ≥ p` such that `s[p … q]` is not a
    substring of `s[0 … q−1]`. Copies may overlap the phrase being built, as in LZ76.
  - The next phrase starts at `q + 1`.
  - If the end is reached while the piece can still be copied, that last piece counts as a
    phrase too.
  - The complexity is the number of phrases. The implementations use the Kaspar-Schuster
    scan, which gives this count.
- **The rules.** `bits` one-dimensional, each 0 or 1, at least one of them.
- **No normalization.** The raw count is returned. The common normalization
  `c·log2(n)/n` is a single line for the caller.

## Consequences

- **Vectors.**
  - The generator parses by the definition above with string searches. That is independent of
    the scan the library uses.
  - It asserts Lempel and Ziv's example: `0001101001000101` parses as
    `0 · 001 · 10 · 100 · 1000 · 101`, which is 6.
  - The values are exact integers.
