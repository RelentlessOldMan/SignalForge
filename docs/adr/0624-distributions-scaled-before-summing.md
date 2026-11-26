# ADR 0624: Distributions divided by their largest value before they are summed

Status: accepted, 2026-11-26. Amends ADRs 0407–0416.

## Context

The ten divergences and distances between discrete distributions (Kullback–Leibler,
Jensen–Shannon, Hellinger, Bhattacharyya, total variation, Pearson chi-square, Rényi, Jeffreys,
cross-entropy, triangular discrimination) normalized each record by its sum of raw values. All
ten are scale-free, but a record whose values are each finite can still sum past the largest
double. The sum is then infinite, every share becomes 0, and the result is wrong. For
`p = (1e308, 9e307, 1e300)` against `q = (1, 2, 3)`, in both languages:

- the Kullback–Leibler, Jeffreys and Rényi divergences and the cross-entropy raised a
  "math domain error" in Python;
- the Bhattacharyya distance and Rényi divergence said the records share no support;
- the Pearson chi-square divergence raised `ZeroDivisionError` in Python, the wrong
  exception;
- the rest returned wrong values: the Hellinger distance gave `1/√2` instead of 0.5535, and
  the total variation distance gave 0.5 instead of 0.49999999474.

## Decision

Each record is checked and its largest value `top` found first. A record whose values are
all 0 is refused as before ("must have a positive sum"). The sum is then taken over
`value/top`, in order, and each share is `(value/top)/sum`. That sum lies between 1 and the
length, so it cannot overflow. C# `DistributionSum` returns the scaled sum and gives `top` as
an `out` argument, and the callers divide `p[i] / pt / ps`. Python builds the same quotients
with `a / top`, element by element, then adds them in the same order.

## Consequences

- Shares can differ from the old ones in the last bit, since they are now two divisions
  rather than one. Every existing vector still passes in both languages, within its
  tolerance.
- Each of the ten generators gained `huge_p` and `huge_q` cases, computed exactly in
  rationals: the records sum to about 1.9e308 and 2.7e308. All 20 failed in both languages
  before the change. Mutations were checked: removing the scaling from Python's
  Kullback–Leibler divergence alone failed its 2 cases, and capping the C# scale at 1, which
  leaves ordinary counts unchanged, failed all 20.
- About 25 other scale-free functions (concentration, inequality and evenness indices, the
  coefficient of variation, the von Neumann ratio and others) fail the same probe.
  `docs/status.md` lists them as a lead.
