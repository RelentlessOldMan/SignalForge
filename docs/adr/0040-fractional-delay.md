# ADR 0040: Fractional delay

Status: accepted, 2026-11-13

## Context

Echoes in a real channel do not fall on the sample grid, and a timing-recovery test needs a
signal delayed by part of a sample. A fractional delay is band-limited interpolation; the
choices are the interpolator (Lagrange, Farrow, windowed sinc), its length, and what happens
near the ends.

## Decision

- `fractional_delay(samples, delay, *, half_width=16)`: a windowed sinc evaluated afresh for each
  output sample, `2·half_width` taps, Kaiser window with `β = 8`.
- One fixed `β` keeps the signature small; `half_width` trades length for accuracy near the band
  edge. With the default, a tone up to a quarter of the sample rate comes through within about
  2e-5 (the window's ripple), and one at 0.4 within about 1.5e-4.
- Samples outside the input are zero and the output is as long as the input, as for
  `multipath`.
- The sinc is set exactly to 0 at non-zero integers, so whole-sample delays are exact shifts.
- `multipath` keeps integer delays; fractional echoes are sums of `fractional_delay` calls.

## Consequences

- Vectors come from a stdlib generator that evaluates the sum term by term with its own I₀
  series.
- A Farrow structure (for time-varying delays) can come later on top of the same definition.
