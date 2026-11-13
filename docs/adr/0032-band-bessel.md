# ADR 0032: Band-pass and band-stop Bessel

Status: accepted, 2026-11-13

## Context

Bessel low-pass and high-pass exist (ADR 0025); the band-pass and band-stop are the last two
designs missing from the IIR family. Every other family's band designs go through one shared
routine: the low-pass prototype's poles, the band transform, and the bilinear transform
(ADR 0016, ADR 0021, ADR 0023).

## Decision

- `bessel_bandpass(order, low, high, sample_rate)` and `bessel_bandstop(...)` feed the Bessel
  prototype's poles (normalized to −3 dB at 1) to that routine, with the gains of the band
  Chebyshev type I (no finite zeros): band-pass `−p_r` for the real pole and `|p_k|` per pair
  section, band-stop 1. So `low` and `high` are the −3 dB points, as for every other band design
  whose edges are not ripple or attenuation edges.
- `1 ≤ order ≤ 10`, the low-pass's limit, for the same reason (the roots of `θ_N` lose accuracy
  above it).

## Consequences

- The band filters inherit the Bessel's magnitude but not its flat delay: the delay is flat in
  the prototype's frequency `x = (t² − W²)/(B·t)`, which is not linear in `f`. The conventions
  say so; anyone who needs a flat delay across a band should shift a low-pass by mixing.
- Expected values: the generator's 50-digit Decimal roots (as for the low-pass) through its own
  band transform, checked against the closed-form `|H|²` and the substituted denominator, plus
  two order-1 cases by hand.
