# ADR 0446: Anderberg's D

Status: accepted, 2026-11-19.

## Context

Anderberg's D of two binary records measures how much better one record predicts the other
than its own most common value does. Guessing the second record from the first, taking the
more common value in each row of the 2x2 table, gets `max(TP, FP) + max(FN, TN)` right;
guessing it with no help gets `max(|B|, n − |B|)` right. Adding the same for the other
direction gives `σ = max(TP, FN) + max(FP, TN) + max(TP, FP) + max(FN, TN)` and
`σ' = max(|A|, n − |A|) + max(|B|, n − |B|)`, and `D = (σ − σ') / (2n)`. From 0 (no gain,
which includes independence) to 1/2 (each record fixes the other, as when they agree or
disagree everywhere with balanced counts).

## Decision

- **The API.**
  - Python: `anderberg_d(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.AnderbergD(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)`.
- **The value.**
  - `σ − σ'` and `2n` are exact integers, each converted to a double once (exact below
    `2⁵³`), then one division.
  - From 0 to 1/2. Symmetric in the two records; unchanged when either record is flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - No further error: `2n` is never zero.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    cell shares, as row and column maxima.
  - The tolerance is `abs 1e-15, rel 1e-15`.
