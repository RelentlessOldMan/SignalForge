# ADR 0451: Stiles' coefficient

Status: accepted, 2026-11-19.

## Context

Stiles' coefficient of two binary records is
`log10(n·(|c| − n/2)² / (|A|·|B|·(n − |A|)·(n − |B|)))` with `c = n·TP − |A|·|B|`, which is
`TP·TN − FN·FP`. The argument of the logarithm is Yates' continuity-corrected chi-square of
the 2x2 table over `n`. It has no fixed ends; it goes to minus infinity as `|c|` nears
`n/2`, and the correction makes it grow again for `|c| < n/2`, so independence (`c = 0`)
does not give the least value.

## Decision

- **The API.**
  - Python: `stiles_coefficient(truth, decision)` in `measurements`, giving a float.
  - C#: `Measurements.StilesCoefficient(ReadOnlySpan<double> truth,
    ReadOnlySpan<double> decision)`.
- **The value.**
  - The exact integers `e = 2·|c| − n`, `n`, `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)`
    are each converted to a double once; the argument is `n · e · e / (4 · u · v)` in that
    order, then the platform's `log10`. `log10` is not correctly rounded, so the two
    languages may differ in the last bits.
  - Symmetric in the two records; unchanged when either record is flipped.
- **The rules.**
  - Records as for the Jaccard index: values only 0 and 1, the same length, at least 1.
  - A constant record is an error: then `u · v = 0`.
  - `2·|c| = n` is an error: the argument is 0 and its logarithm is minus infinity.

## Consequences

- The cost is one pass.
- **Vectors.**
  - The generator counts the table directly, forms the argument in rationals as
    `(|TP·TN − FN·FP| − n/2)²·n / (|A|·|B|·(n − |A|)·(n − |B|))` and takes its correctly
    rounded `log10` in 40-digit decimals.
  - The tolerance is `abs 1e-14, rel 1e-14`.
