# ADR 0186: Energy-time curve

Status: accepted, 2026-11-16. It builds on the analytic signal of ADR 0185.

## Context

An energy-time curve (ETC) shows how an impulse response's energy arrives over time:

- the direct sound;
- the reflections;
- the decay.

A plain `h²` swings to zero twice per cycle, so the usual curve is the squared envelope of the
analytic signal, `|h + j·H{h}|²`, in dB. Tools differ on three choices:

- the reference level (the peak, the total energy, or an absolute level);
- whether the curve is smoothed;
- what happens at zero.

## Decision

- **The API.** In `measurements`:
  - Python: `energy_time_curve(impulse_response)`.
  - C#: `Measurements.EnergyTimeCurve(impulseResponse)`.
  - The result has one value per sample.
- **The definition.** `ETC[n] = 10·log10(|z[n]|² / max |z|²)` dB, with `z` the
  `analytic_signal` of ADR 0185.
  - The peak is 0 dB.
  - A zero envelope gives `−inf`, as in conventions (Decibels).
  - There is no smoothing. A caller who wants it smooths the curve.
- **The rules.**
  - The input follows the analytic-signal rules: real, one-dimensional, finite and not empty.
  - It must not be all zero.
  - Anything else is `invalid_argument`.

## Consequences

- **Vectors.** They come from closed forms:
  - impulses, whose analytic signals are worked by hand in ADR 0185's vectors, including
    circular shifts;
  - an AM tone at bin frequencies, whose envelope is exactly `1 + m·cos`, giving
    `20·log10(env / (1 + m))`;
  - a constant, which stays at 0 dB.
