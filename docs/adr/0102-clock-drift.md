# ADR 0102: Sample clock drift

Status: accepted, 2026-11-16. Extends [ADR 0045](0045-clock-offset.md).

## Context

An oscillator warming up or cooling down does not hold a constant offset: it drifts. A timing
loop that follows a fixed offset may still lose a drifting one, so the channel model needs a
clock whose offset changes across the input.

## Decision

- Python `clock_drift(samples, ppm_start, ppm_end, *, half_width=16)`. C#
  `Channel.ClockDrift(samples, ppmStart, ppmEnd, halfWidth = 16)`.
- The offset is linear in **input** time: `p(t) = p₀ + (p₁ − p₀)·t/(N − 1)` over `0 ≤ t ≤ N − 1`.
  So `ppm_start` holds at the first input sample and `ppm_end` at the last, whatever the output
  length, which is not known in advance.
- The receiver steps from `t_n` by `1 + p(t_n)/1e6`. With `r = 1 + p₀/1e6` and
  `d = (p₁ − p₀)/1e6/(N − 1)`, that is `t_{n+1} = r + (1 + d)·t_n`, `t₀ = 0`.
  - The recurrence has the closed form `t_n = r·((1 + d)ⁿ − 1)/d`. It is computed as
    `r·expm1(n·log1p(d))/d`, which keeps the digits of a small `d`. `(1 + d)ⁿ` with `pow` would
    lose them, because `1 + d` rounds.
  - A running sum would give each language the same rounding, but its error grows with `n`. The
    closed form has a few ulps of relative error at every `n`, and both languages evaluate every
    `t_n` independently.
  - With `d = 0` (equal offsets, or `N ≤ 1`), `t_n = n·r` exactly as `clock_offset` computes it, so
    the two give the same output bit for bit.
- The output is `y[n] = z(t_n)`, read by the fractional delay kernel exactly as `clock_offset`
  does, for `n = 0, 1, …` while `t_n ≤ N − 1`. Reading stops at the first `t_n` past the end.
  Empty input gives empty output.
- Both offsets are finite with `|·| ≤ 1e5`, as in ADR 0045. Then every step is at least 0.9, so
  `t_n` rises. `half_width` is an integer `≥ 1`.

## Consequences

- Expected values come from a stdlib generator.
  - It runs the recurrence in exact rational arithmetic (`fractions.Fraction`), from the
    floating-point `r` and `d`. It then reads each `t_n` with its own kernel. That route shares
    nothing with `expm1` and `log1p`.
  - Equal offsets are checked against the `clock_offset` definition.
  - The output length for `N = 11`, `p₀ = 0`, `p₁ = 1e5` is worked by hand: `d = 0.01`, and
    `t_n ≤ 10` needs `1.01ⁿ ≤ 1.1`, so `n ≤ 9.58` and there are 10 outputs.
- The two languages can differ in the last bit of `t_n`. A `t_n` that lands within a few ulps of
  `N − 1` could then end one output apart. Vectors avoid that edge.
