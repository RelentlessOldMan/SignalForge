# ADR 0477: The chord distance of two binary records

Status: accepted, 2026-11-20.

## Context

The chord distance of two binary records is `sqrt(2·(1 − o))` with
`o = TP / sqrt(|A|·|B|)`, the Ochiai coefficient (`ochiai_coefficient`): the length of the
chord between the two records scaled to unit length. 0 when the records are equal, √2 when
they share no 1.

## Decision

- **The API.**
  - Python: `chord_distance(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.ChordDistance(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - `o` is the exact integer `TP` converted to a double over the root of the exact integer
    `|A|·|B|` converted to a double once, as for the Ochiai coefficient; then
    `sqrt(2·(1 − o))`.
  - From 0 to √2. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A record with no 1 is an error: `o` is then 0/0.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in 40-digit decimals with
    correctly rounded square roots.
  - The tolerance is `abs 1e-14, rel 1e-14`: `1 − o` loses digits when `o` is near 1.
