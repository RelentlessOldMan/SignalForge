# ADR 0263: Crossfade

Status: accepted, 2026-11-17.

## Context

Joining two recordings end to start makes a click unless the first fades out while the second
fades in over a shared stretch. The ramps are those of the fades (ADR 0262). In a crossfade they
are complementary, so the two gains add to 1. Unlike a fade, no overlap sample has a gain of
exactly 0 or 1, so every overlap sample mixes both signals.

## Decision

- **The API.**
  - Python: `crossfade(a, b, overlap, *, shape="linear")` in `dsp`.
  - C#: `Dsp.Crossfade(a, b, overlap, shape = FadeShape.Linear)`.
  - The output is complex if either input is, as in NumPy.
- **The value.** With lengths `Nₐ`, `N_b` and `L = overlap`, the output has `Nₐ + N_b − L`
  samples:
  - `a[0 … Nₐ−L−1]`, then
  - for `k` in `[0, L)`: `t = (k+1)/(L+1)`, `w = r(t)` with the ADR 0262 ramp, and
    `y = a[Nₐ−L+k]·(1 − w) + b[k]·w`, evaluated in that order;
  - then `b[L …]`.
  - With `L = 0` it is plain concatenation.
  - A complex sample is scaled part by part.
  - The gains are linear, or equal-gain for the raised cosine, since `1 − r(t) = r(1 − t)`.
    The level dips in the middle of a crossfade between uncorrelated signals.
- **The rules.**
  - `overlap` must be an integer in `[0, min(Nₐ, N_b)]`.
  - `shape` must be one of the two names.
  - Both inputs must be finite and non-empty.

## Consequences

- **Vectors.**
  - The linear cases use `L = 3`, so `t = 1/4, 1/2, 3/4` and the values are exact in rationals.
  - The cosine cases use the stdlib `math.cos`.
  - The tolerance is `abs 1e-15`.
