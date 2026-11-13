# ADR 0033: All-pass sections

Status: accepted, 2026-11-13

## Context

Phase equalization (flattening a filter's group delay, or building a Hilbert pair or a notch as
`(1 ± A)/2`) needs all-pass sections. Two implementations could parameterize them differently:
by pole radius and angle, by Q, or by frequencies. Frequencies are what a user knows, and the
bilinear transform makes them exact.

## Decision

- `allpass_first_order(cutoff, sample_rate)`: `[c, 1, 0, 1, c, 0]` with
  `c = (t − 1)/(t + 1)`, `t = tan(π·cutoff/fs)`, the bilinear transform of `(K − s)/(K + s)`:
  phase exactly `−π/2` at the cutoff.
- `allpass_second_order(center, bandwidth, sample_rate)`:
  `[−c, d(1 − c), 1, 1, d(1 − c), −c]` with `c` of the bandwidth and `d = −cos(2π·center/fs)`:
  phase exactly `−π` at the center, and the `−π/2` and `−3π/2` points exactly `bandwidth`
  apart. `(1 − A)/2` is then the second-order band-pass with those −3 dB edges.
- Each returns one section in the usual `[b0, b1, b2, a0, a1, a2]` form, so `sos_response`,
  `sos_group_delay`, `IirFilter` and cascading with other designs work unchanged.

## Consequences

- The center is where the phase is `−π`, which is not the arithmetic middle of the two edges:
  `cos(π(f₁ + f₂)/fs) = cos(2π·center/fs)·cos(π·bandwidth/fs)`, written in the conventions.
- No design-to-a-delay-target routine yet: choosing sections to equalize a given filter is a
  later slice.
- Expected values: four cases by hand, and the generator checks `H = −j, −1, j` at the phase
  points with the edges from their closed form.
