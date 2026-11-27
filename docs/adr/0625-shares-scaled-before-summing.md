# ADR 0625: Records of shares divided by their largest value before they are summed

Status: accepted, 2026-11-26. Amends ADRs 0523–0538 and 0549.

## Context

Sixteen concentration, diversity and evenness indices turn a record into shares of its sum:
the Herfindahl index, concentration ratio, Hall–Tideman, Kwoka and Hannah–Kay indices,
Pielou's evenness, the Gini–Simpson and Berger–Parker indices, Heip's, Simpson's,
Camargo's, Bulla's, Hill ratio, Alatalo's and Sheldon's evenness, and Strong's dominance.
All are scale-free, but a record whose values are each finite can still sum past the largest
double. The sum is then infinite and every share is 0 or NaN. For `(1e308, 9e307, 1e300)`,
in both languages, each returned a wrong value, NaN, or (Simpson's and Hill ratio evenness in
Python) a `ZeroDivisionError`. Smith and Wilson's evenness works on logarithms of the values
and was already right.

## Decision

As in ADR 0624: once the values are checked, the record is divided by its largest value, and
the existing sums and shares are formed from those quotients. The sum then lies between 1 and
the record length and cannot overflow. In Python, `x = x / top` replaces the record before
the sum. A record whose values are all 0 is refused, as before. C# `ScaledToLargest` returns
the quotients when the largest value is positive and finite, and the values unchanged
otherwise, so the existing checks refuse a bad record with the same error, in the same order,
as before.

## Consequences

- Shares can differ from the old ones in the last bit, since they now take two divisions
  instead of one. Every existing vector still passes in both languages, within its
  tolerance.
- Each of the 17 generators, including Smith and Wilson's, gained an exact `huge` case on
  `(1e308, 9e307, 1e300)`. The 16 for these functions failed in both languages before the
  change. Mutation check: scaling by `min(top, 1)`, which leaves ordinary records unchanged,
  failed all 16 in each language.
- Other scale-free functions still fail the same probe: the inequality indices (Gini, Theil,
  Hoover, mean log deviation, Palma, quintile share, Bonferroni, Zenga, Wolfson), the Lorenz
  curve, the coefficient of variation, the von Neumann ratio, time irreversibility, Horn's
  overlap, and the Pearson and distance correlations. `docs/status.md` lists them as a lead.
