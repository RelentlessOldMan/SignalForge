# ADR 0313: PolyBLEP pulse-width modulation

Status: accepted, 2026-11-18.

## Context

The PWM of ADR 0312 is naive and aliases like the square. The PolyBLEP square (ADR 0311)
smooths both edges of a fixed-duty square. Applying its rule with the duty of each sample
gives the usual cheap band-limited PWM of software synthesizers.

## Decision

- **The API.**
  - Python: `polyblep_pwm(duty, sample_rate, frequency, amplitude=1, phase=0)` in `waveforms`.
  - C#: `Waveforms.PolyblepPwm`, same arguments, `duty` a `ReadOnlySpan<double>`.
  - One output sample per `duty` value, as for `pwm`.
- **The value.** The rule of ADR 0311 with `d = duty[n]` at sample `n`: `v = u − d`, plus 1
  when `u < d`; `y = s + A·r(u) − A·r(v)`, `s` the naive PWM sample. A constant `duty` gives
  the PolyBLEP square.
- **What it leaves out.** The residual assumes the edge moves with the phase at rate `dt`. When
  the duty also moves, the falling edge's true rate is `dt − Δduty` a sample. The usual form
  ignores that, and so does this one: the error is second order for a duty that changes
  slowly against the pitch.
- **The rules.** Those of `pwm`, and `|f| ≤ fs/2` as for the PolyBLEP oscillators.

## Consequences

- **Vectors.** Expected values come from the rule in exact rationals, rounded once. Per sample
  the output is continuous in `u`, as for the PolyBLEP square, so a rounding of `u` across an
  edge changes it by a rounding only. The tolerance is `abs 1e-12, rel 1e-12`.
- **Code.** The PolyBLEP square and this share one per-sample edge helper.
