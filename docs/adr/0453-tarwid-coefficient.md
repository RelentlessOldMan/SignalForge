# ADR 0453: Tarwid's coefficient

Status: accepted, 2026-11-19.

## Context

Tarwid's coefficient of two binary records is `(n·TP − |A|·|B|) / (n·TP + |A|·|B|)`, with
`|A|` and `|B|` the counts of 1: the shared 1s set against the `|A|·|B|/n` that chance would
give, as a difference over a sum. 0 when `TP` is what chance gives, −1 when no 1 is shared,
and below 1 always, nearing it as the shared 1s far exceed chance.

## Decision

- **The API.**
  - Python: `tarwid_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.TarwidCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - Numerator and denominator exact integers, each converted to a double once, then one
    division.
  - From −1 to below 1. Symmetric in the two records.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A zero denominator is an error: that is a record with no 1 (then `TP` is 0 too).

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly and forms the value in rationals from the
    shares, as `(TP/n − pA·pB) / (TP/n + pA·pB)`.
  - The tolerance is `abs 1e-15, rel 1e-15`.
